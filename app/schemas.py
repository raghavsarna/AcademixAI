"""Request and response models for the JSON API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Digests


class DigestSummary(ORMModel):
    id: int
    title: str
    description: str
    image_url: str | None
    published_at: datetime


class DigestDetail(DigestSummary):
    content: str


# ---- Papers


class PaperSummary(ORMModel):
    id: str
    title: str
    authors: list[str]
    source: str | None
    doi: str | None
    created_at: datetime


class MyPaper(PaperSummary):
    uploaded_at: datetime
    filename: str


class PaperDetail(PaperSummary):
    publication_date: str | None
    keywords: list[str]
    abstract: str | None
    summary: str | None
    main_findings: str | None
    methodology: str | None


class UploadResult(BaseModel):
    paper: PaperSummary
    created: bool  # False if the paper had already been analysed
    url: str  # page to open for this paper


# ---- Chat


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
