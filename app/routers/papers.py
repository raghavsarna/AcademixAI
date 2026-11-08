from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models import Paper, Upload, UploadJob, User
from app.rate_limit import chat_limit, upload_limit
from app.schemas import ChatRequest, ChatResponse, MyPaper, PaperDetail, PaperSummary, UploadJobOut
from app.security import CurrentUser, DbSession
from app.services import chat, jobs
from app.services.pdf import InvalidPDF
from app.storage import LocalStorage, get_storage

router = APIRouter(prefix="/api/papers", tags=["papers"])


def get_paper_or_404(db: DbSession, paper_id: str) -> Paper:
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paper not found.")
    return paper


@router.get("", response_model=list[MyPaper])
def my_papers(user: CurrentUser, db: DbSession) -> list[MyPaper]:
    """Papers the logged-in user has uploaded, newest first."""
    uploads = db.scalars(
        select(Upload).where(Upload.user_id == user.id).order_by(Upload.created_at.desc(), Upload.id.desc())
    )
    return [
        MyPaper(
            **PaperSummary.model_validate(u.paper).model_dump(),
            uploaded_at=u.created_at,
            filename=u.filename,
            what_changed=u.paper.what_changed,
        )
        for u in uploads
    ]


@router.post(
    "", response_model=UploadJobOut, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(upload_limit)]
)
async def upload_paper(
    response: Response,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    storage: Annotated[LocalStorage, Depends(get_storage)],
    file: Annotated[UploadFile, File(description="A research paper as a PDF")],
) -> UploadJob:
    """Upload a PDF to be explained. Answers at once with a job to poll.

    202: the paper is being analysed; poll GET /api/papers/jobs/{id}.
    200: this file was explained before, and the job is already ready.
    """
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    try:
        job = await run_in_threadpool(jobs.start_upload, db, user, file.filename or "paper.pdf", data, storage)
    except InvalidPDF as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from None
    if job.status == "ready":
        response.status_code = status.HTTP_200_OK
    else:
        background.add_task(jobs.run_job, job.id, storage)
    return job


def get_job_or_404(db: DbSession, user: User, job_id: str) -> UploadJob:
    job = db.get(UploadJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found.")
    return job


@router.get("/jobs", response_model=list[UploadJobOut])
def my_jobs(user: CurrentUser, db: DbSession) -> list[UploadJob]:
    """Your recent uploads and how far each one has got, newest first."""
    return jobs.recent_jobs(db, user)


@router.get("/jobs/{job_id}", response_model=UploadJobOut)
def get_job(job_id: str, user: CurrentUser, db: DbSession) -> UploadJob:
    return get_job_or_404(db, user, job_id)


@router.post("/jobs/{job_id}/retry", response_model=UploadJobOut, dependencies=[Depends(upload_limit)])
def retry_job(
    job_id: str,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    storage: Annotated[LocalStorage, Depends(get_storage)],
) -> UploadJob:
    """Try a failed upload again, from the PDF that was kept."""
    job = get_job_or_404(db, user, job_id)
    if not jobs.retry(db, job):
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a failed upload can be tried again.")
    background.add_task(jobs.run_job, job.id, storage)
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_job(
    job_id: str, user: CurrentUser, db: DbSession, storage: Annotated[LocalStorage, Depends(get_storage)]
) -> None:
    """Remove an upload from your list. A paper it produced stays in your papers."""
    job = get_job_or_404(db, user, job_id)
    try:
        jobs.dismiss(db, job, storage)
    except ValueError:
        raise HTTPException(status.HTTP_409_CONFLICT, "This upload is still being explained.") from None


@router.get("/{paper_id}", response_model=PaperDetail)
def get_paper(paper_id: str, db: DbSession) -> Paper:
    """A paper's analysis. Anyone with the link can view it."""
    return get_paper_or_404(db, paper_id)


@router.post("/{paper_id}/chat", response_model=ChatResponse, dependencies=[Depends(chat_limit)])
async def chat_about_paper(paper_id: str, body: ChatRequest, db: DbSession, _: CurrentUser) -> ChatResponse:
    paper = get_paper_or_404(db, paper_id)
    return ChatResponse(reply=await chat.answer(chat.paper_context(paper), body.message, body.level))
