"""Request and response models for the JSON API."""

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, computed_field


def _assume_utc(value: datetime) -> datetime:
    # SQLite returns timestamps without a timezone; they are stored in UTC
    return value if value.tzinfo else value.replace(tzinfo=UTC)


UTCDateTime = Annotated[datetime, AfterValidator(_assume_utc)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserOut(ORMModel):
    id: int
    email: EmailStr
    username: str
    created_at: UTCDateTime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Papers

Depth = Literal["plain", "student", "expert"]


class BuildsOn(BaseModel):
    work: str
    relation: str


class PaperSummary(ORMModel):
    id: str
    title: str
    authors: list[str]
    source: str | None
    doi: str | None
    origin: str
    created_at: UTCDateTime


class PaperCard(PaperSummary):
    """A paper as it appears in an edition."""

    arxiv_id: str | None
    source_url: str | None
    categories: list[str]
    short_name: str | None
    change_type: str | None
    what_changed: str | None
    why_it_matters: str | None
    builds_on: list[BuildsOn]


class MyPaper(PaperSummary):
    uploaded_at: UTCDateTime
    filename: str
    what_changed: str | None


class PaperDetail(PaperCard):
    publication_date: str | None
    keywords: list[str]
    abstract: str | None
    explanations: dict[str, str]
    main_findings: str | None
    methodology: str | None


class UploadJobOut(ORMModel):
    """An upload being explained. Poll it until status is "ready" (then open url) or "failed"."""

    id: str
    filename: str
    status: str  # queued, reading, analysing, ready or failed
    error: str | None
    paper_id: str | None
    paper_title: str | None
    created_at: UTCDateTime
    updated_at: UTCDateTime

    @computed_field
    @property
    def url(self) -> str | None:
        return f"/papers/{self.paper_id}" if self.status == "ready" and self.paper_id else None


# ---- Editions


class Theme(BaseModel):
    name: str
    summary: str
    papers: list[str]


class EditionSummary(ORMModel):
    id: int
    edition_date: date
    headline: str
    overview: str
    papers_scanned: int
    entry_count: int


class EditionEntryOut(ORMModel):
    rank: int
    paper: PaperCard


class EditionDetail(ORMModel):
    id: int
    edition_date: date
    headline: str
    overview: str
    papers_scanned: int
    themes: list[Theme]
    entries: list[EditionEntryOut]
    previous_date: date | None = None
    next_date: date | None = None


# ---- Chat


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    level: Depth = "student"


class ChatResponse(BaseModel):
    reply: str
