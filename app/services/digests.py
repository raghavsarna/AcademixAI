"""Generating the daily AI research digest from new arXiv papers."""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import arxiv
from sqlalchemy.orm import Session

from app import llm
from app.models import Digest
from app.services.markdown import strip_leading_title, to_markdown

logger = logging.getLogger(__name__)

ARXIV_QUERY = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV"

DIGEST_PROMPT = """You are a science communicator who makes AI research accessible to a general audience.
Today is {today}. Below are the latest research papers from arXiv in AI, machine learning,
computer vision and NLP. Write an engaging, accurate newsletter about them in markdown:

1. Start with a title on the first line, formatted as "# Title".
2. An introduction explaining why these papers matter.
3. A "## Major Trends" section describing 2-3 trends across the papers.
4. A "## Spotlight on Five Interesting Papers" section. For each paper use a "###" heading
   with its title, then explain in simple terms what it does, why it matters to an ordinary
   person, and an analogy that makes the idea click. Link to the paper's URL.
5. A "## Conclusion" section that looks ahead.

Use proper heading levels (not bold text for headings), **bold** for key terms and
*italics* for emphasis, with one blank line before each heading.

Papers:
{papers}
"""


@dataclass
class ArxivPaper:
    title: str
    authors: list[str]
    abstract: str
    published: str
    url: str
    categories: list[str]


def fetch_recent_papers(max_results: int = 150) -> list[ArxivPaper]:
    """Fetch the newest AI papers from arXiv (blocking network call)."""
    search = arxiv.Search(
        query=ARXIV_QUERY,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
    return [
        ArxivPaper(
            title=r.title.strip(),
            authors=[a.name for a in r.authors],
            abstract=" ".join(r.summary.split()),
            published=r.published.strftime("%Y-%m-%d"),
            url=r.entry_id,
            categories=list(r.categories),
        )
        for r in client.results(search)
    ]


def build_prompt(papers: list[ArxivPaper], today: str) -> str:
    listing = "\n\n".join(
        f"Paper {i}:\nTitle: {p.title}\nAuthors: {', '.join(p.authors[:8])}\n"
        f"Published: {p.published}\nCategories: {', '.join(p.categories)}\n"
        f"Abstract: {p.abstract}\nURL: {p.url}"
        for i, p in enumerate(papers, 1)
    )
    return DIGEST_PROMPT.format(today=today, papers=listing)


def extract_title(markdown: str, today: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].replace("*", "").strip()
            if len(title) >= 10:
                return title[:500]
    return f"AI Research Digest: {today}"


def extract_description(markdown: str, today: str) -> str:
    """First real paragraph of the introduction, trimmed to a sentence or two."""
    for block in re.split(r"\n\s*\n", markdown):
        block = block.strip()
        if len(block) > 80 and not block.startswith(("#", "-", "*", ">")):
            plain = re.sub(r"[*_`]", "", " ".join(block.split()))
            sentences = re.split(r"(?<=[.!?])\s+", plain)
            description = ""
            for sentence in sentences:
                if len(description) + len(sentence) > 280:
                    break
                description = f"{description} {sentence}".strip()
            return description or plain[:277] + "..."
    return f"The most interesting new AI research from {today}, explained for everyone."


async def generate_digest(db: Session, max_papers: int = 150) -> Digest:
    now = datetime.now(UTC)
    today = now.strftime("%Y-%m-%d")

    papers = await asyncio.to_thread(fetch_recent_papers, max_papers)
    if not papers:
        raise RuntimeError("No papers were returned by arXiv")
    logger.info("Fetched %d papers from arXiv", len(papers))

    markdown = to_markdown(await llm.generate(build_prompt(papers, today))) or ""
    if len(markdown) < 200:
        raise RuntimeError("The model returned an unusually short digest")

    title = extract_title(markdown, today)
    digest = Digest(
        title=title,
        description=extract_description(markdown, today),
        content=strip_leading_title(markdown, title),
        image_url=None,
        published_at=now,
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest
