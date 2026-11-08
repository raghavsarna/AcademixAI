from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select

from app.config import settings
from app.models import Paper, Upload
from app.rate_limit import chat_limit, upload_limit
from app.schemas import ChatRequest, ChatResponse, MyPaper, PaperDetail, PaperSummary, UploadResult
from app.security import CurrentUser, DbSession
from app.services import chat
from app.services.papers import ingest_pdf
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
        )
        for u in uploads
    ]


@router.post("", response_model=UploadResult, dependencies=[Depends(upload_limit)])
async def upload_paper(
    response: Response,
    user: CurrentUser,
    db: DbSession,
    storage: Annotated[LocalStorage, Depends(get_storage)],
    file: Annotated[UploadFile, File(description="A research paper as a PDF")],
) -> UploadResult:
    """Upload a PDF. The paper is analysed by the model and added to your papers."""
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    try:
        result = await ingest_pdf(db, user, file.filename or "paper.pdf", data, storage)
    except InvalidPDF as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from None
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return UploadResult(
        paper=PaperSummary.model_validate(result.paper),
        created=result.created,
        url=f"/papers/{result.paper.id}",
    )


@router.get("/{paper_id}", response_model=PaperDetail)
def get_paper(paper_id: str, db: DbSession) -> Paper:
    """A paper's analysis. Anyone with the link can view it."""
    return get_paper_or_404(db, paper_id)


@router.post("/{paper_id}/chat", response_model=ChatResponse, dependencies=[Depends(chat_limit)])
async def chat_about_paper(paper_id: str, body: ChatRequest, db: DbSession, _: CurrentUser) -> ChatResponse:
    paper = get_paper_or_404(db, paper_id)
    return ChatResponse(reply=await chat.answer(chat.paper_context(paper), body.message))
