from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.models import Digest
from app.rate_limit import chat_limit
from app.schemas import ChatRequest, ChatResponse, DigestDetail, DigestSummary
from app.security import CurrentUser, DbSession
from app.services import chat

router = APIRouter(prefix="/api/digests", tags=["digests"])


def _get_digest(db: DbSession, digest_id: int) -> Digest:
    digest = db.get(Digest, digest_id)
    if digest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Digest not found.")
    return digest


@router.get("", response_model=list[DigestSummary])
def list_digests(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Digest]:
    """Digests, newest first."""
    query = select(Digest).order_by(Digest.published_at.desc(), Digest.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(query))


@router.get("/{digest_id}", response_model=DigestDetail)
def get_digest(digest_id: int, db: DbSession) -> Digest:
    return _get_digest(db, digest_id)


@router.post("/{digest_id}/chat", response_model=ChatResponse, dependencies=[Depends(chat_limit)])
async def chat_about_digest(digest_id: int, body: ChatRequest, db: DbSession, _: CurrentUser) -> ChatResponse:
    digest = _get_digest(db, digest_id)
    return ChatResponse(reply=await chat.answer(chat.digest_context(digest), body.message))
