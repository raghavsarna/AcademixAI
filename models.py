from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    preferences = Column(Text, nullable=True)  # For storing user preferences as JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    uploads = relationship("UserUpload", back_populates="user")
    chats = relationship("Chat", back_populates="user")

class Paper(Base):
    __tablename__ = "papers"
    doi = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(String, nullable=False)
    source = Column(String, nullable=False)  # Journal or conference name
    data = Column(Text, nullable=True)  # Raw content
    summary = Column(Text, nullable=True)  # Processed summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    uploads = relationship("UserUpload", back_populates="paper")
    chats = relationship("Chat", back_populates="paper")
    podcast = relationship("CustomPaperPodcast", back_populates="paper", uselist=False)

class Newsletter(Base):
    __tablename__ = "newsletter"
    summary_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    chats = relationship("Chat", back_populates="newsletter")
    podcast = relationship("NewsletterPodcast", back_populates="newsletter", uselist=False)

class UserUpload(Base):
    __tablename__ = "user_uploads"
    upload_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doi = Column(String, ForeignKey("papers.doi"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    original_pdf = Column(String, nullable=True)  # Path to the PDF file
    summary = Column(Text, nullable=True)  # User-provided summary

    # Relationships
    user = relationship("User", back_populates="uploads")
    paper = relationship("Paper", back_populates="uploads")

class Chat(Base):
    __tablename__ = "chats"
    chat_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_doi = Column(String, ForeignKey("papers.doi"), nullable=True)
    summary_id = Column(Integer, ForeignKey("newsletter.summary_id"), nullable=True)
    messages = Column(Text, nullable=True)  # Store chat history as JSON string

    # Relationships
    user = relationship("User", back_populates="chats")
    paper = relationship("Paper", back_populates="chats")
    newsletter = relationship("Newsletter", back_populates="chats")

class NewsletterPodcast(Base):
    __tablename__ = "newsletter_podcasts"
    summary_id = Column(Integer, ForeignKey("newsletter.summary_id"), primary_key=True)
    content = Column(Text, nullable=False)
    podcast_url = Column(String, nullable=False)

    # Relationships
    newsletter = relationship("Newsletter", back_populates="podcast")

class CustomPaperPodcast(Base):
    __tablename__ = "custom_paper_podcasts"
    doi = Column(String, ForeignKey("papers.doi"), primary_key=True)
    summary = Column(Text, nullable=False)
    podcast_url = Column(String, nullable=False)

    # Relationships
    paper = relationship("Paper", back_populates="podcast")

class Research(Base):
    __tablename__ = "research"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(String, nullable=False)
    doi = Column(String, unique=True, index=True)
    publication_date = Column(String)
    venue = Column(String)  # Journal or conference name
    abstract = Column(Text)
    keywords = Column(String)
    methodology = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())