"""Retrieval over a paper's full text, so chat answers come from the paper itself.

A paper is split into passages that follow its sections and pages, and each passage is embedded.
For a question, passages are ranked two ways, by keyword match (BM25) and by embedding similarity,
and the two rankings are merged (reciprocal rank fusion). If embeddings are unavailable the keyword
ranking is used alone, so chat keeps working without them.
"""

import asyncio
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app import llm
from app.config import settings
from app.llm import LLMError
from app.models import Paper, PaperChunk
from app.services import pdf

logger = logging.getLogger(__name__)

TARGET_CHARS = 1000  # a passage closes at the first sentence end past this length
MAX_CHARS = 1600  # and is cut here whatever happens
OVERLAP_CHARS = 220  # text carried into the next passage so a point split across two is still found
MIN_CHARS = 80  # shorter passages are noise (stray captions, page furniture)
MAX_CHUNKS = 400

PAGE_BREAK = "\f"  # pdf.extract_text separates pages with a form feed

KNOWN_SECTIONS = {
    "abstract", "introduction", "background", "related work", "preliminaries", "method", "methods",
    "methodology", "approach", "experiments", "experimental setup", "results", "evaluation", "analysis",
    "discussion", "limitations", "conclusion", "conclusions", "future work", "acknowledgements",
    "acknowledgments", "references", "bibliography", "appendix",
}  # fmt: skip
REFERENCE_SECTIONS = {"references", "bibliography"}
THANKS_SECTIONS = {"acknowledgements", "acknowledgments"}

SECTION_NUMBER = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.?$")
APPENDIX_NUMBER = re.compile(r"^([A-H](?:\.\d{1,2}){0,2})\.?$")
NUMBERED_HEADING = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+(\S.*)$")
SENTENCE_END = re.compile(r"[.!?:][\"')\]]*$")


@dataclass
class Passage:
    section: str | None
    page: int
    text: str


def _looks_like_title(line: str) -> bool:
    """A section title: short, starts with a capital letter, mostly letters, no closing full stop."""
    words = line.split()
    if not line or not line[0].isupper() or not 1 <= len(words) <= 9 or len(line) > 80:
        return False
    if line.endswith((".", ",", ";")) or line.startswith("[") or any(c in line for c in "%*=<>"):
        return False
    letters = sum(c.isalpha() for c in line)
    return letters / max(1, len(line.replace(" ", ""))) > 0.6


def _follows(number: str, previous: tuple[int, ...] | None) -> bool:
    """Whether a section number can come next. Rejects numbers that are really table or figure values."""
    parts = tuple(int(p) for p in number.split("."))
    if any(p == 0 for p in parts[1:]) or any(p > 30 for p in parts):
        return False
    if previous is None:
        return parts in ((1,), (2,))  # the first numbered section
    if parts[0] == previous[0]:
        return len(parts) > 1  # a subsection of the current section
    return parts[0] == previous[0] + 1 and (len(parts) == 1 or parts[1:] == (1,) * (len(parts) - 1))


def split_into_passages(text: str) -> list[Passage]:
    """Split a paper's text into passages that keep track of their section and page."""
    lines: list[tuple[str, int]] = []
    for page_number, page in enumerate(text.split(PAGE_BREAK), start=1):
        lines += [(line.strip(), page_number) for line in page.split("\n")]

    passages: list[Passage] = []
    section: str | None = None
    # Passages are not kept from the reference list (until an appendix starts) or the acknowledgements
    # (until the next section)
    skipping: str | None = None
    last_number: tuple[int, ...] | None = None
    buffer: list[str] = []
    buffer_page = 1

    def flush(carry: bool) -> None:
        nonlocal buffer, buffer_page
        body = _join(buffer)
        if len(body) >= MIN_CHARS and not skipping:
            passages.append(Passage(section, buffer_page, body))
        if carry and len(body) > OVERLAP_CHARS:
            tail = body[-OVERLAP_CHARS:]
            buffer = [tail[tail.find(" ") + 1 :]]
        else:
            buffer = []

    i = 0
    while i < len(lines):
        line, page = lines[i]
        next_line = lines[i + 1][0] if i + 1 < len(lines) else ""
        heading = None
        number = line.rstrip(".")
        if SECTION_NUMBER.match(line) and _looks_like_title(next_line) and _follows(number, last_number):
            heading, i = f"{number} {next_line}", i + 1
            last_number = tuple(int(p) for p in number.split("."))
        elif skipping and APPENDIX_NUMBER.match(line) and _looks_like_title(next_line):
            heading, i = f"{number} {next_line}", i + 1
        elif (
            (match := NUMBERED_HEADING.match(line))
            and _looks_like_title(match.group(2))
            and _follows(match.group(1), last_number)
        ):
            heading = f"{match.group(1)} {match.group(2)}"
            last_number = tuple(int(p) for p in match.group(1).split("."))
        elif line[:1].isupper() and line.lower().rstrip(":") in KNOWN_SECTIONS:
            heading = line.rstrip(":").title() if line.isupper() else line.rstrip(":")

        if heading:
            flush(carry=False)
            name = re.sub(r"^[\dA-H.]+\s+", "", heading).lower()
            is_appendix = name.startswith("appendix") or bool(APPENDIX_NUMBER.match(heading.split()[0]))
            if name in REFERENCE_SECTIONS:
                skipping = "references"
            elif name in THANKS_SECTIONS:
                skipping = skipping or "thanks"
            elif skipping == "references" and not is_appendix:
                pass  # a stray title-like line inside the reference list
            else:
                skipping = None
                section = heading[:120]
            buffer_page = page
            i += 1
            continue

        if line:
            if not buffer:
                buffer_page = page
            buffer.append(line)
            length = sum(len(part) + 1 for part in buffer)
            if (length >= TARGET_CHARS and SENTENCE_END.search(line)) or length >= MAX_CHARS:
                flush(carry=True)
                buffer_page = page
        i += 1
    flush(carry=False)
    if not passages:
        # A very short document (a one-page abstract, say) is still worth searching, as one passage
        whole = _join([line for line, _ in lines if line])
        if whole:
            passages.append(Passage(None, 1, whole[:MAX_CHARS]))
    return passages[:MAX_CHUNKS]


def _join(lines: list[str]) -> str:
    """Join PDF lines back into prose, rejoining words hyphenated across a line break."""
    text = ""
    for line in lines:
        rejoin = text.endswith("-") and line[:1].islower()  # a word hyphenated across the line break
        text = text[:-1] + line if rejoin else f"{text} {line}".strip()
    return re.sub(r"\s+", " ", text).strip()


# ---- Ranking

STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "how", "in", "is", "it",
        "its", "of", "on", "or", "that", "the", "this", "to", "was", "were", "what", "when", "which", "who", "why",
        "with", "does", "do", "did", "can", "could", "would", "should", "their", "they", "them", "these", "those",
        "than", "then", "there", "about", "into", "paper", "we", "our", "you", "your",
    }
)  # fmt: skip
TOKEN = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


def bm25_rank(question: str, documents: list[str], k1: float = 1.5, b: float = 0.75) -> list[int]:
    """Indices of the documents that match the question's words, best first (Okapi BM25)."""
    query = set(tokenize(question))
    docs = [tokenize(d) for d in documents]
    if not query or not docs:
        return []
    average = sum(len(d) for d in docs) / len(docs) or 1
    frequency = Counter(term for d in docs for term in set(d))
    scores = []
    for index, tokens in enumerate(docs):
        counts = Counter(tokens)
        score = 0.0
        for term in query:
            if not counts[term]:
                continue
            idf = math.log(1 + (len(docs) - frequency[term] + 0.5) / (frequency[term] + 0.5))
            score += idf * counts[term] * (k1 + 1) / (counts[term] + k1 * (1 - b + b * len(tokens) / average))
        if score > 0:
            scores.append((score, index))
    return [index for _, index in sorted(scores, reverse=True)]


def cosine_rank(query: list[float], vectors: list[list[float] | None]) -> list[int]:
    """Indices of the vectors most similar to the query, best first."""
    query_norm = math.sqrt(sum(x * x for x in query)) or 1
    scores = []
    for index, vector in enumerate(vectors):
        if not vector:
            continue
        norm = math.sqrt(sum(x * x for x in vector)) or 1
        scores.append((sum(a * b for a, b in zip(query, vector, strict=True)) / (query_norm * norm), index))
    return [index for _, index in sorted(scores, reverse=True)]


def fuse(rankings: list[list[int]], k: int = 60) -> list[int]:
    """Reciprocal rank fusion: items ranked high in any list rise to the top."""
    scores: Counter[int] = Counter()
    for ranking in rankings:
        for rank, index in enumerate(ranking):
            scores[index] += 1 / (k + rank + 1)
    return [index for index, _ in scores.most_common()]


# ---- Indexing

_locks: dict[str, asyncio.Lock] = {}


async def fetch_arxiv_text(arxiv_id: str) -> str | None:
    """The full text of an arXiv paper, from its PDF. None if it can't be fetched or read."""
    limit = settings.max_arxiv_pdf_mb * 1024 * 1024
    try:
        headers = {"User-Agent": "AcademixAI (research paper explainer)"}
        async with (
            httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client,
            client.stream("GET", f"https://arxiv.org/pdf/{arxiv_id}") as response,
        ):
            response.raise_for_status()
            data = bytearray()
            async for part in response.aiter_bytes():
                data += part
                if len(data) > limit:
                    logger.warning("arXiv PDF %s is over %d MB; not indexing it", arxiv_id, settings.max_arxiv_pdf_mb)
                    return None
        return await run_in_threadpool(pdf.extract_text, bytes(data))
    except (httpx.HTTPError, pdf.InvalidPDF) as e:
        logger.warning("Couldn't fetch the full text of arXiv %s: %s", arxiv_id, e)
        return None


def is_indexed(db: Session, paper: Paper) -> bool:
    return db.scalar(select(PaperChunk.id).where(PaperChunk.paper_id == paper.id).limit(1)) is not None


async def ensure_index(db: Session, paper: Paper) -> bool:
    """Make sure the paper's passages are stored, building them the first time.

    The text is the uploaded PDF's, or for a paper from an edition, fetched from arXiv. Embeddings
    are added when the embedding model answers; without them, keyword ranking still works.
    Returns False when the paper has no full text to search.
    """
    if is_indexed(db, paper):
        return True
    lock = _locks.setdefault(paper.id, asyncio.Lock())
    async with lock:
        db.expire(paper)
        if is_indexed(db, paper):
            return True
        text = paper.full_text
        if not text and paper.arxiv_id:
            text = await fetch_arxiv_text(paper.arxiv_id)
            if text:
                paper.full_text = text
        if not text:
            return False
        passages = split_into_passages(text)
        if not passages:
            return False
        try:
            vectors: list[list[float] | None] = list(
                await llm.embed([f"{p.section or ''}\n{p.text}" for p in passages], "RETRIEVAL_DOCUMENT")
            )
        except LLMError as e:
            logger.warning("Indexing %s without embeddings: %s", paper.id, e)
            vectors = [None] * len(passages)
        for position, (passage, vector) in enumerate(zip(passages, vectors, strict=True)):
            db.add(
                PaperChunk(
                    paper_id=paper.id,
                    position=position,
                    section=passage.section,
                    page=passage.page,
                    text=passage.text,
                    embedding=[round(x, 6) for x in vector] if vector else None,
                )
            )
        db.commit()
        logger.info("Indexed %s: %d passages", paper.id, len(passages))
        return True


async def retrieve(db: Session, paper: Paper, question: str, limit: int = 6) -> list[PaperChunk]:
    """The passages of the paper that best answer the question, best first."""
    chunks = list(db.scalars(select(PaperChunk).where(PaperChunk.paper_id == paper.id).order_by(PaperChunk.position)))
    if not chunks:
        return []
    rankings = [bm25_rank(question, [f"{c.section or ''} {c.text}" for c in chunks])]
    vectors = [c.embedding for c in chunks]
    if any(vectors):
        try:
            query = (await llm.embed([question], "RETRIEVAL_QUERY"))[0]
            rankings.append(cosine_rank(query, vectors))
        except LLMError as e:
            logger.warning("Query embedding failed, ranking by keywords only: %s", e)
    order = fuse([r for r in rankings if r])
    return [chunks[i] for i in order[:limit]]
