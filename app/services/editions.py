"""Building a day's edition: which new arXiv papers changed the field, and what each one changes.

Pipeline (about a dozen model calls per day):
1. Fetch the day's new papers in AI, ML, NLP and vision from arXiv.
2. Triage: one call picks the papers that change the field most.
3. Analyse each pick from its abstract: what changed, what it builds on, three explanation depths.
4. One call writes the day's headline, overview and themes.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import arxiv
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import llm
from app.models import Edition, EditionEntry, Paper
from app.services.analysis import (
    CHANGE_FIELDS_SPEC,
    CHANGE_RULES,
    as_list,
    as_text,
    normalize_change_fields,
    parse_json_reply,
    strip_em_dashes,
)

logger = logging.getLogger(__name__)

CATEGORIES = ("cs.AI", "cs.LG", "cs.CL", "cs.CV")

TRIAGE_PROMPT = """You are the editor of a daily changelog of AI research. Below are {count} papers submitted
to arXiv on {day}. Pick the {picks} papers that change the field the most: new methods with broad use,
new state-of-the-art claims, important benchmarks or datasets, and results that challenge common practice.
Prefer variety across subfields. Skip incremental work, narrow applications and position pieces.

Reply with ONLY a JSON object: {{"picks": [{{"id": "arXiv id", "reason": "one short sentence"}}]}},
most important first.

Papers:
{papers}
"""

PAPER_PROMPT = (
    """You write a daily changelog of AI research for three audiences: curious non-experts, students
and practitioners. Analyse this new arXiv paper from its abstract. Reply with ONLY a JSON object:

{{
  "keywords": ["keyword", "keyword"],
"""
    + CHANGE_FIELDS_SPEC.replace("{", "{{").replace("}", "}}")
    + """
}}

"""
    + CHANGE_RULES
    + """
- You only have the abstract, so keep explanations to what it supports.

Title: {title}
Authors: {authors}
Categories: {categories}
Abstract:
<<<
{abstract}
>>>
"""
)

OVERVIEW_PROMPT = """You edit a daily changelog of AI research. These are today's entries ({day}), most
important first, each with what it changes. Write the edition's front matter and reply with ONLY a JSON object:

{{
  "headline": "under 90 characters, a plain statement of the most concrete, checkable change today: who or what
    did what, with the number if there is one. Example shape: 'Agent swarms that reason in latent space cut a
    60-minute search to under 8'",
  "overview": "two or three sentences. Open with the strongest result, then name two or three other specific
    entries by their short name and what each one changes",
  "themes": [{{"name": "2 to 4 words", "summary": "one sentence", "paper_ids": ["arXiv id", "..."]}}]
}}

Rules:
- Use 2 to 4 themes, each covering at least one entry.
- Only state what the entries state.
- Never use these words: highlights, advancements, landscape, emphasize, explores, delve, cutting-edge,
  groundbreaking, revolutionize. No colon teasers and no em dashes.

Entries:
{entries}
"""


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: date
    url: str


def _arxiv_id(entry_id: str) -> str:
    return re.sub(r"v\d+$", "", entry_id.rstrip("/").split("/")[-1])


def fetch_papers(day: date | None = None, max_results: int = 1000) -> tuple[date, list[ArxivPaper]]:
    """Papers first submitted on `day`, or on the most recent day with submissions (blocking)."""
    query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    if day is not None:
        query = f"({query}) AND submittedDate:[{day:%Y%m%d}0000 TO {day:%Y%m%d}2359]"
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
    papers = [
        ArxivPaper(
            arxiv_id=_arxiv_id(r.entry_id),
            title=" ".join(r.title.split()),
            authors=[a.name for a in r.authors],
            abstract=" ".join(r.summary.split()),
            categories=list(r.categories),
            published=r.published.date(),
            url=f"https://arxiv.org/abs/{_arxiv_id(r.entry_id)}",
        )
        for r in client.results(search)
    ]
    if not papers:
        raise RuntimeError(f"arXiv returned no papers for {day or 'recent days'}")
    target = day or max(p.published for p in papers)
    return target, [p for p in papers if p.published == target]


async def triage(papers: list[ArxivPaper], day: date, picks: int) -> list[ArxivPaper]:
    listing = "\n\n".join(
        f"id: {p.arxiv_id}\ntitle: {p.title}\ncategories: {', '.join(p.categories[:4])}\nabstract: {p.abstract[:450]}"
        for p in papers
    )
    reply = await llm.generate(
        TRIAGE_PROMPT.format(count=len(papers), day=day.isoformat(), picks=picks, papers=listing), json_output=True
    )
    by_id = {p.arxiv_id: p for p in papers}
    chosen: list[ArxivPaper] = []
    for item in parse_json_reply(reply).get("picks", []):
        paper = by_id.get(_arxiv_id(str(item.get("id", ""))) if isinstance(item, dict) else "")
        if paper and paper not in chosen:
            chosen.append(paper)
    if not chosen:
        raise RuntimeError("Triage picked no papers")
    return chosen[:picks]


async def analyze_arxiv_paper(paper: ArxivPaper) -> dict:
    reply = await llm.generate(
        PAPER_PROMPT.format(
            title=paper.title,
            authors=", ".join(paper.authors[:12]),
            categories=", ".join(paper.categories),
            abstract=paper.abstract,
        ),
        json_output=True,
    )
    data = parse_json_reply(reply)
    return {"keywords": as_list(data.get("keywords"))[:8], **normalize_change_fields(data)}


async def write_front_matter(papers: list[Paper], day: date) -> dict:
    entries = "\n\n".join(f"id: {p.arxiv_id}\ntitle: {p.title}\nwhat changed: {p.what_changed}" for p in papers)
    data = parse_json_reply(
        await llm.generate(OVERVIEW_PROMPT.format(day=day.isoformat(), entries=entries), json_output=True)
    )
    id_to_paper = {p.arxiv_id: p.id for p in papers}
    themes = []
    for theme in data.get("themes") or []:
        if not isinstance(theme, dict):
            continue
        ids = [id_to_paper[i] for i in as_list(theme.get("paper_ids")) if i in id_to_paper]
        name = as_text(theme.get("name"), 60)
        if name and ids:
            themes.append(
                {"name": name, "summary": strip_em_dashes(as_text(theme.get("summary"))) or "", "papers": ids}
            )
    headline = strip_em_dashes(as_text(data.get("headline"), 300)) or f"What changed in AI research on {day:%B %-d}"
    overview = strip_em_dashes(as_text(data.get("overview"))) or ""
    return {"headline": headline, "overview": overview, "themes": themes[:4]}


def _upsert_paper(db: Session, source: ArxivPaper, fields: dict) -> Paper:
    paper = db.scalar(select(Paper).where(Paper.arxiv_id == source.arxiv_id))
    if paper is None:
        paper = Paper(
            origin="arxiv",
            arxiv_id=source.arxiv_id,
            doi=f"10.48550/arXiv.{source.arxiv_id}",
            title=source.title[:500],
            authors=source.authors,
            source="arXiv",
            source_url=source.url,
            publication_date=source.published.isoformat(),
            categories=source.categories,
            abstract=source.abstract,
            **fields,
        )
        db.add(paper)
        db.flush()
    return paper


async def build_edition(
    db: Session, day: date | None = None, picks: int = 10, max_results: int = 1000, replace: bool = False
) -> Edition:
    day, papers = await asyncio.to_thread(fetch_papers, day, max_results)
    existing = db.scalar(select(Edition).where(Edition.edition_date == day))
    if existing is not None and not replace:
        logger.info("Edition for %s already exists", day)
        return existing
    logger.info("Fetched %d papers submitted on %s", len(papers), day)

    chosen = await triage(papers, day, picks)
    known = {p.arxiv_id: p for p in db.scalars(select(Paper).where(Paper.arxiv_id.in_([c.arxiv_id for c in chosen])))}

    # Analyse new picks a few at a time to stay inside the model's per-minute limit
    semaphore = asyncio.Semaphore(3)

    async def analyse(source: ArxivPaper) -> tuple[ArxivPaper, dict | None]:
        if source.arxiv_id in known:
            return source, None
        async with semaphore:
            try:
                return source, await analyze_arxiv_paper(source)
            except Exception:
                logger.exception("Skipping %s: analysis failed", source.arxiv_id)
                return source, {}

    results = await asyncio.gather(*(analyse(c) for c in chosen))
    entries: list[Paper] = []
    for source, fields in results:
        if fields == {}:
            continue
        paper = known.get(source.arxiv_id) or _upsert_paper(db, source, fields)
        if paper.what_changed and paper.explanations:
            entries.append(paper)
    if not entries:
        raise RuntimeError("No paper could be analysed")

    front = await write_front_matter(entries, day)
    if existing is not None:
        db.delete(existing)
        db.flush()
    edition = Edition(edition_date=day, papers_scanned=len(papers), **front)
    edition.entries = [EditionEntry(paper_id=p.id, rank=i) for i, p in enumerate(entries, 1)]
    db.add(edition)
    db.commit()
    db.refresh(edition)
    return edition


def recent_days(count: int, until: date | None = None) -> list[date]:
    """The last `count` weekdays up to `until` (arXiv gets few submissions at weekends)."""
    day = until or (datetime.now(UTC).date() - timedelta(days=1))
    days: list[date] = []
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return days
