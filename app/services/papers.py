"""Turning an uploaded PDF into an analysed paper."""

import json
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
from app.services.markdown import to_markdown
from app.storage import LocalStorage

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are a research paper analyser. Below is the text of a research paper.
Extract the following and reply with ONLY a JSON object with exactly these keys:

{{
  "title": "the paper's title",
  "authors": ["Author One", "Author Two"],
  "doi": "the DOI, e.g. 10.1234/abcd, or null if the text does not contain one",
  "publication_date": "YYYY-MM-DD, or as precise as the text allows, or null",
  "source": "journal or conference name, or null",
  "abstract": "the paper's abstract",
  "keywords": ["keyword", "keyword"],
  "summary": "about 500 words explaining the paper to a non-technical reader, in markdown with
    paragraphs, bullet points and emphasis",
  "main_findings": "the key findings and contributions as a markdown bulleted list in one string",
  "methodology": "the methods used, in markdown with short sections and bullet points"
}}

Rules:
- Only use a DOI that appears in the text (often in the header, footer or first page). Never invent one.
- If the paper is long, focus on the title, abstract, introduction and conclusion.

Paper text:
<<<
{text}
>>>
"""

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


class AnalysisError(Exception):
    """The model's reply could not be turned into a paper."""


@dataclass
class IngestResult:
    paper: Paper
    created: bool  # False if an existing analysis was reused


def parse_json_reply(reply: str) -> dict[str, Any]:
    """Parse the model's JSON reply, tolerating code fences or text around the object."""
    candidates = [reply.strip()]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", reply, re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1).strip())
    braces = re.search(r"\{.*\}", reply, re.DOTALL)
    if braces:
        candidates.append(braces.group(0))
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    raise AnalysisError("The model's reply was not valid JSON")


def normalize_doi(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    doi = value.strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.IGNORECASE)
    return doi if DOI_PATTERN.match(doi) else None


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r",|;| and ", value) if part.strip()]
    return []


def _as_text(value: Any, max_length: int | None = None) -> str | None:
    if value is None or (isinstance(value, str) and value.strip().lower() in ("", "null", "none", "n/a")):
        return None
    text = str(value).strip()
    return text[:max_length] if max_length else text


def normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    """Map the model's reply onto Paper fields, fixing types and odd values."""
    return {
        "title": _as_text(data.get("title"), 500) or "Untitled paper",
        "authors": _as_list(data.get("authors")),
        "doi": normalize_doi(data.get("doi")),
        "publication_date": _as_text(data.get("publication_date"), 50),
        "source": _as_text(data.get("source"), 500),
        "keywords": _as_list(data.get("keywords")),
        "abstract": to_markdown(_as_text(data.get("abstract"))),
        "summary": to_markdown(data.get("summary")),
        "main_findings": to_markdown(data.get("main_findings")),
        "methodology": to_markdown(data.get("methodology")),
    }


async def analyze_text(text: str) -> dict[str, Any]:
    prompt = ANALYSIS_PROMPT.format(text=text[: settings.max_pdf_chars])
    reply = await llm.generate(prompt, json_output=True)
    try:
        return normalize_analysis(parse_json_reply(reply))
    except AnalysisError:
        logger.error("Unparseable analysis reply: %s", reply[:2000])
        raise


def _link_upload(db: Session, user: User, paper: Paper, filename: str, pdf_key: str | None) -> None:
    exists = db.scalar(select(Upload).where(Upload.user_id == user.id, Upload.paper_id == paper.id))
    if exists is None:
        db.add(Upload(user_id=user.id, paper_id=paper.id, filename=filename[:255], pdf_key=pdf_key))


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

    # Same paper (by DOI) uploaded as a different file
    if fields["doi"]:
        paper = db.scalar(select(Paper).where(Paper.doi == fields["doi"]))
        if paper is not None:
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
        paper = db.scalar(select(Paper).where(Paper.file_hash == file_hash))
        if paper is None and fields["doi"]:
            paper = db.scalar(select(Paper).where(Paper.doi == fields["doi"]))
        if paper is None:
            raise
        _link_upload(db, user, paper, filename, None)
        db.commit()
        return IngestResult(paper, created=False)
    return IngestResult(paper, created=True)
