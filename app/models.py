"""Database models."""

import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.db import Base


def new_public_id() -> str:
    """Random, unguessable id used in paper URLs."""
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uploads: Mapped[list["Upload"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Paper(Base):
    """A research paper analysed by the model. Shared between users who upload the same paper."""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_public_id)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)  # sha256 of the PDF
    title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    source: Mapped[str | None] = mapped_column(String(500))
    publication_date: Mapped[str | None] = mapped_column(String(50))
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    abstract: Mapped[str | None] = mapped_column(Text)
    # Where the paper came from: "arxiv" (daily editions) or "upload"
    origin: Mapped[str] = mapped_column(String(16), default="upload", server_default="upload")
    arxiv_id: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500))
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    # What the paper claims is new, and the kind of change (see services.analysis.CHANGE_TYPES)
    what_changed: Mapped[str | None] = mapped_column(Text)
    change_type: Mapped[str | None] = mapped_column(String(32))
    why_it_matters: Mapped[str | None] = mapped_column(Text)
    # Earlier work the paper says it builds on: [{"work": ..., "relation": ...}]
    builds_on: Mapped[list[dict]] = mapped_column(JSON, default=list)
    # The same explanation at three depths: {"plain": ..., "student": ..., "expert": ...}
    explanations: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    main_findings: Mapped[str | None] = mapped_column(Text)
    methodology: Mapped[str | None] = mapped_column(Text)
    # Extracted text, kept for retrieval-based chat. Not loaded unless accessed.
    full_text: Mapped[str | None] = deferred(mapped_column(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uploads: Mapped[list["Upload"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    entries: Mapped[list["EditionEntry"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class Upload(Base):
    """A user's upload of a paper. Uploads are private to the user who made them."""

    __tablename__ = "uploads"
    __table_args__ = (UniqueConstraint("user_id", "paper_id", name="uq_upload_user_paper"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    pdf_key: Mapped[str | None] = mapped_column(String(255))  # where the PDF is kept in storage
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="uploads")
    paper: Mapped[Paper] = relationship(back_populates="uploads")


class Edition(Base):
    """One day's changelog of AI research: the papers that moved the field, ranked."""

    __tablename__ = "editions"

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    headline: Mapped[str] = mapped_column(String(300))
    overview: Mapped[str] = mapped_column(Text)  # what moved today, in a few sentences
    # Threads running through the day's papers: [{"name": ..., "summary": ..., "papers": [paper ids]}]
    themes: Mapped[list[dict]] = mapped_column(JSON, default=list)
    papers_scanned: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entries: Mapped[list["EditionEntry"]] = relationship(
        back_populates="edition", cascade="all, delete-orphan", order_by="EditionEntry.rank"
    )


class EditionEntry(Base):
    __tablename__ = "edition_entries"
    __table_args__ = (UniqueConstraint("edition_id", "paper_id", name="uq_entry_edition_paper"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("editions.id", ondelete="CASCADE"), index=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer)

    edition: Mapped[Edition] = relationship(back_populates="entries")
    paper: Mapped[Paper] = relationship(back_populates="entries")
