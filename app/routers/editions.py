from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import Edition, EditionEntry
from app.rate_limit import chat_limit
from app.schemas import ChatRequest, ChatResponse, EditionDetail, EditionSummary
from app.security import CurrentUser, DbSession
from app.services import chat

router = APIRouter(prefix="/api/editions", tags=["editions"])


def _load(db: DbSession, edition_date: date | None) -> Edition:
    query = select(Edition).options(selectinload(Edition.entries).selectinload(EditionEntry.paper))
    query = (
        query.where(Edition.edition_date == edition_date)
        if edition_date
        else query.order_by(Edition.edition_date.desc()).limit(1)
    )
    edition = db.scalar(query)
    if edition is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No edition for that date.")
    return edition


def _detail(db: DbSession, edition: Edition) -> EditionDetail:
    previous = db.scalar(select(func.max(Edition.edition_date)).where(Edition.edition_date < edition.edition_date))
    following = db.scalar(select(func.min(Edition.edition_date)).where(Edition.edition_date > edition.edition_date))
    detail = EditionDetail.model_validate(edition)
    detail.previous_date, detail.next_date = previous, following
    return detail


@router.get("", response_model=list[EditionSummary])
def list_editions(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EditionSummary]:
    """Editions, newest first."""
    counts = select(EditionEntry.edition_id, func.count().label("n")).group_by(EditionEntry.edition_id).subquery()
    rows = db.execute(
        select(Edition, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.edition_id == Edition.id)
        .order_by(Edition.edition_date.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        EditionSummary(
            id=e.id,
            edition_date=e.edition_date,
            headline=e.headline,
            overview=e.overview,
            papers_scanned=e.papers_scanned,
            entry_count=n,
        )
        for e, n in rows
    ]


@router.get("/latest", response_model=EditionDetail)
def latest_edition(db: DbSession) -> EditionDetail:
    return _detail(db, _load(db, None))


@router.get("/{edition_date}", response_model=EditionDetail)
def get_edition(edition_date: date, db: DbSession) -> EditionDetail:
    return _detail(db, _load(db, edition_date))


@router.post("/{edition_date}/chat", response_model=ChatResponse, dependencies=[Depends(chat_limit)])
async def chat_about_edition(edition_date: date, body: ChatRequest, db: DbSession, _: CurrentUser) -> ChatResponse:
    edition = _load(db, edition_date)
    return ChatResponse(reply=await chat.answer(chat.edition_context(edition), body.message, body.level))
