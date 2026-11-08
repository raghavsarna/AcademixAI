"""Turning an uploaded PDF into an analysed paper."""

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app import llm
from app.config import settings
from app.models import Paper, Upload, User
from app.services import pdf
from app.services.analysis import (
    CHANGE_FIELDS_SPEC,
    CHANGE_RULES,
    AnalysisError,
    as_list,
    as_text,
    normalize_change_fields,
    parse_json_reply,
    strip_em_dashes,
)
from app.services.markdown import to_markdown
from app.storage import LocalStorage

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = (
    """You are a research paper analyser. Below is the text of a research paper.
Reply with ONLY a JSON object with exactly these keys:

{{
  "title": "the paper's title",
  "authors": ["Author One", "Author Two"],
  "doi": "the DOI, e.g. 10.1234/abcd, or null if the text does not contain one",
  "arxiv_id": "the arXiv identifier, e.g. 2310.06825, or null if the text does not contain one",
  "publication_date": "YYYY-MM-DD, or as precise as the text allows, or null",
  "source": "journal or conference name, or null",
  "abstract": "the paper's abstract",
  "keywords": ["keyword", "keyword"],
"""
    + CHANGE_FIELDS_SPEC.replace("{", "{{").replace("}", "}}")
    + """,
  "main_findings": "the key findings and contributions as a markdown bulleted list in one string",
  "methodology": "the methods used, in markdown with short sections and bullet points"
}}

"""
    + CHANGE_RULES
    + """
- Only use a DOI or arXiv id that appears in the text (often in the header, footer or first page).
- If the paper is long, focus on the title, abstract, introduction and conclusion.

Paper text:
<<<
{text}
>>>
"""
)

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")
ARXIV_ID_PATTERN = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?$")


@dataclass
class IngestResult:
    paper: Paper
    created: bool  # False if an existing analysis was reused


def normalize_doi(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    doi = value.strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.IGNORECASE)
    return doi if DOI_PATTERN.match(doi) else None


def normalize_arxiv_id(value: Any, doi: str | None = None) -> str | None:
    """arXiv id without version, from an explicit id or an arXiv DOI (10.48550/arXiv.<id>)."""
    candidates = [value] if isinstance(value, str) else []
    if doi and doi.lower().startswith("10.48550/arxiv."):
        candidates.append(doi.split(".", 2)[-1])
    for candidate in candidates:
        match = ARXIV_ID_PATTERN.match(re.sub(r"^(arxiv:\s*)", "", candidate.strip(), flags=re.IGNORECASE))
        if match:
            return match.group(1)
    return None


def normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    """Map the model's reply onto Paper fields, fixing types and odd values."""
    doi = normalize_doi(data.get("doi"))
    arxiv_id = normalize_arxiv_id(data.get("arxiv_id"), doi)
    return {
        "title": as_text(data.get("title"), 500) or "Untitled paper",
        "authors": as_list(data.get("authors")),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "source_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else (f"https://doi.org/{doi}" if doi else None),
        "publication_date": as_text(data.get("publication_date"), 50),
        "source": as_text(data.get("source"), 500),
        "keywords": as_list(data.get("keywords")),
        "abstract": to_markdown(as_text(data.get("abstract"))),
        "main_findings": strip_em_dashes(to_markdown(data.get("main_findings"))),
        "methodology": strip_em_dashes(to_markdown(data.get("methodology"))),
        **normalize_change_fields(data),
    }


async def analyze_text(text: str, attempts: int = 2) -> dict[str, Any]:
    """Analyse a paper's text. A reply that is not valid JSON gets one fresh attempt."""
    prompt = ANALYSIS_PROMPT.format(text=text[: settings.max_pdf_chars])
    for attempt in range(1, attempts + 1):
        reply = await llm.generate(prompt, json_output=True)
        try:
            return normalize_analysis(parse_json_reply(reply))
        except AnalysisError:
            logger.warning("Unparseable analysis reply (attempt %d): %s", attempt, reply[:500])
    raise AnalysisError("The model's reply was not valid JSON")


def _link_upload(db: Session, user: User, paper: Paper, filename: str, pdf_key: str | None) -> None:
    exists = db.scalar(select(Upload).where(Upload.user_id == user.id, Upload.paper_id == paper.id))
    if exists is None:
        db.add(Upload(user_id=user.id, paper_id=paper.id, filename=filename[:255], pdf_key=pdf_key))


def _find_existing(db: Session, fields: dict[str, Any]) -> Paper | None:
    if fields.get("doi"):
        paper = db.scalar(select(Paper).where(Paper.doi == fields["doi"]))
        if paper is not None:
            return paper
    if fields.get("arxiv_id"):
        return db.scalar(select(Paper).where(Paper.arxiv_id == fields["arxiv_id"]))
    return None


def _enrich(paper: Paper, fields: dict[str, Any], text: str, file_hash: str) -> None:
    """A known paper analysed from its abstract gains the full-text analysis from an upload."""
    if paper.main_findings:
        return
    for key in ("main_findings", "methodology", "explanations", "what_changed", "why_it_matters", "builds_on"):
        if fields.get(key):
            setattr(paper, key, fields[key])
    paper.full_text = text
    if paper.file_hash is None:
        paper.file_hash = file_hash


async def ingest_pdf(db: Session, user: User, filename: str, data: bytes, storage: LocalStorage) -> IngestResult:
    """Validate, analyse and store an uploaded PDF, reusing earlier analyses where possible."""
    pdf.validate_pdf(data, settings.max_upload_mb * 1024 * 1024)
    file_hash = pdf.sha256(data)

    # Same file uploaded before: reuse it without calling the model again
    paper = db.scalar(select(Paper).where(Paper.file_hash == file_hash))
    if paper is not None:
        _link_upload(db, user, paper, filename, None)
        db.commit()
        return IngestResult(paper, created=False)

    text = await run_in_threadpool(pdf.extract_text, data)
    fields = await analyze_text(text)

    # Same paper (by DOI or arXiv id) already known, e.g. from a daily edition
    paper = _find_existing(db, fields)
    if paper is not None:
        _enrich(paper, fields, text, file_hash)
        _link_upload(db, user, paper, filename, None)
        db.commit()
        return IngestResult(paper, created=False)

    pdf_key = storage.save(data)
    paper = Paper(file_hash=file_hash, full_text=text, **fields)
    db.add(paper)
    try:
        db.flush()
        _link_upload(db, user, paper, filename, pdf_key)
        db.commit()
    except IntegrityError:
        # Another request stored the same paper at the same moment
        db.rollback()
        storage.delete(pdf_key)
        paper = db.scalar(select(Paper).where(Paper.file_hash == file_hash)) or _find_existing(db, fields)
        if paper is None:
            raise
        _link_upload(db, user, paper, filename, None)
        db.commit()
        return IngestResult(paper, created=False)
    return IngestResult(paper, created=True)
