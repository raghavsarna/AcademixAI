"""Explaining uploads in the background.

An upload is checked and stored straight away, and answered with a job. The analysis, which can
take a minute when the model is busy, then runs after the response, and the job records each
stage so the website can show real progress and survive the reader leaving the page.

Jobs run inside the API process. A job cut short by a restart is marked failed on startup and
can be retried, because its PDF is kept until the job succeeds.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.db import SessionLocal
from app.llm import LLMError
from app.models import UploadJob, User
from app.services import pdf, retrieval
from app.services.analysis import AnalysisError
from app.services.papers import analyze_text, link_known_file, store_analysis
from app.storage import LocalStorage

logger = logging.getLogger(__name__)

ACTIVE = ("queued", "reading", "analysing")

BUSY = "The AI service is busy right now. Try again in a minute."
UNREADABLE = "The AI couldn't make sense of this paper. Try again, or try another PDF."
INTERRUPTED = "This was interrupted when the server restarted. Try again."
UNEXPECTED = "Something went wrong on our side. Try again."


def start_upload(db: Session, user: User, filename: str, data: bytes, storage: LocalStorage) -> UploadJob:
    """Check an upload and create its job. Raises pdf.InvalidPDF for files that can't be used.

    A file explained before is linked at once and its job is already "ready". Otherwise the PDF is
    stored and the job is "queued" for run_job.
    """
    filename = (filename or "paper.pdf")[:255]
    pdf.validate_pdf(data, settings.max_upload_mb * 1024 * 1024)
    pdf.extract_text(data)  # reject scanned or damaged PDFs now, while the reader is still here
    file_hash = pdf.sha256(data)

    paper = link_known_file(db, user, filename, file_hash)
    if paper is not None:
        job = UploadJob(user_id=user.id, filename=filename, file_hash=file_hash, status="ready", paper_id=paper.id)
    else:
        job = UploadJob(user_id=user.id, filename=filename, file_hash=file_hash, pdf_key=storage.save(data))
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _set_status(db: Session, job: UploadJob, status: str, error: str | None = None) -> None:
    job.status = status
    job.error = error
    db.commit()


async def run_job(job_id: str, storage: LocalStorage) -> None:
    """Analyse a queued upload. Never raises: every outcome is recorded on the job."""
    with SessionLocal() as db:
        job = db.get(UploadJob, job_id)
        if job is None or job.status not in ACTIVE:
            return
        try:
            user = db.get(User, job.user_id)
            if user is None or not job.pdf_key:
                raise RuntimeError(f"Job {job_id} has no user or no stored PDF")
            _set_status(db, job, "reading")
            data = await run_in_threadpool(storage.read, job.pdf_key)
            text = await run_in_threadpool(pdf.extract_text, data)

            _set_status(db, job, "analysing")
            fields = await analyze_text(text)

            result = store_analysis(db, user, job.filename, text, job.file_hash, job.pdf_key, fields, storage)
            if not result.created:
                job.pdf_key = None  # the PDF was not needed: an existing paper was reused
            job.paper_id = result.paper.id
            _set_status(db, job, "ready")
            # Prepare the paper for chat now, so the reader's first question is quick. Not fatal:
            # chat builds the index itself on the first question if this fails.
            try:
                await retrieval.ensure_index(db, result.paper)
            except Exception:
                logger.exception("Job %s: indexing for chat failed", job_id)
        except Exception as e:
            db.rollback()
            if isinstance(e, LLMError):
                logger.warning("Job %s: model unavailable: %s", job_id, e)
                message = BUSY
            elif isinstance(e, AnalysisError):
                logger.warning("Job %s: unusable model reply", job_id)
                message = UNREADABLE
            elif isinstance(e, pdf.InvalidPDF):
                message = str(e)
            else:
                logger.exception("Job %s failed", job_id)
                message = UNEXPECTED
            job = db.get(UploadJob, job_id)
            if job is not None:
                _set_status(db, job, "failed", message)


def recent_jobs(db: Session, user: User, limit: int = 20) -> list[UploadJob]:
    return list(
        db.scalars(
            select(UploadJob)
            .where(UploadJob.user_id == user.id)
            .order_by(UploadJob.created_at.desc(), UploadJob.id)
            .limit(limit)
        )
    )


def retry(db: Session, job: UploadJob) -> bool:
    """Queue a failed job again. False when it can't be retried (not failed, or its PDF is gone)."""
    if job.status != "failed" or not job.pdf_key:
        return False
    _set_status(db, job, "queued")
    return True


def dismiss(db: Session, job: UploadJob, storage: LocalStorage) -> None:
    """Forget a job. Its PDF is deleted too, unless a paper is using it."""
    if job.status in ACTIVE:
        raise ValueError("A job can't be dismissed while it runs")
    if job.pdf_key and job.status != "ready":
        storage.delete(job.pdf_key)
    db.delete(job)
    db.commit()


def fail_interrupted() -> int:
    """On startup, no job can still be running: mark any left unfinished as failed."""
    with SessionLocal() as db:
        result = db.execute(
            update(UploadJob).where(UploadJob.status.in_(ACTIVE)).values(status="failed", error=INTERRUPTED)
        )
        db.commit()
        return result.rowcount or 0
