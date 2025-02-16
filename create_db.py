#!/usr/bin/env python
"""
create_research_db.py

This script defines and processes the database schema for a research paper summary website.
It features user accounts, research paper processing, newsletters, user uploads, a chat interface,
and podcasts generated from summaries.

The script performs the following:
  1. Defines tables: Users, Papers, Newsletter, UserUpload, Chat, NewsletterPodcast, CustomPaperPodcast.
  2. Creates the database and tables.
  3. Inserts sample data for testing purposes.
  4. Provides a function to process a new paper upload, checking for duplicate DOIs.
  
The database connection uses SQLite for simplicity, but can be updated for PostgreSQL if needed.
"""

import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Create the base class for declarative models
Base = declarative_base()


# ----------------------
# Model Definitions
# ----------------------

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    preferences = Column(JSON)  # Can store preferences as JSON

    def __repr__(self):
        return f"<User(email='{self.email}')>"


class Paper(Base):
    __tablename__ = 'papers'
    doi = Column(String, primary_key=True)  # DOI as primary key; unique by definition
    title = Column(String, nullable=False)
    authors = Column(String, nullable=False)
    source = Column(String, nullable=False)
    data = Column(Text)       # Raw data/content of the paper
    summary = Column(Text)    # Processed summary of the paper

    def __repr__(self):
        return f"<Paper(doi='{self.doi}', title='{self.title}')>"


class Newsletter(Base):
    __tablename__ = 'newsletter'
    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)  # Added title attribute
    date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    picture = Column(String)   # URL or path to the picture
    content = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Newsletter(summary_id='{self.summary_id}', title='{self.title}', date='{self.date}')>"


class UserUpload(Base):
    __tablename__ = 'user_upload'
    upload_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    doi = Column(String, nullable=False)  # Will be used to cross-check against Papers before processing
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    original_pdf = Column(String)  # Path or URL to the uploaded PDF
    summary = Column(Text)

    # Relationship to easily access user details
    user = relationship("User", backref="uploads")

    def __repr__(self):
        return f"<UserUpload(upload_id='{self.upload_id}', user_id='{self.user_id}', doi='{self.doi}')>"


class Chat(Base):
    __tablename__ = 'chat'
    chat_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    paper_doi = Column(String, ForeignKey('papers.doi'), nullable=True)
    summary_id = Column(Integer, ForeignKey('newsletter.summary_id'), nullable=True)
    messages = Column(JSON)  # Stores chat messages as JSON

    # Relationships to access linked records
    user = relationship("User", backref="chats")
    paper = relationship("Paper", backref="chats")
    newsletter = relationship("Newsletter", backref="chats")

    def __repr__(self):
        return f"<Chat(chat_id='{self.chat_id}', user_id='{self.user_id}')>"


class NewsletterPodcast(Base):
    __tablename__ = 'newsletter_podcast'
    # summary_id serves both as primary key and a foreign key to Newsletter
    summary_id = Column(Integer, ForeignKey('newsletter.summary_id'), primary_key=True)
    content = Column(Text, nullable=False)
    podcast_url = Column(String, nullable=False)

    newsletter = relationship("Newsletter", backref="podcast")

    def __repr__(self):
        return f"<NewsletterPodcast(summary_id='{self.summary_id}')>"


class CustomPaperPodcast(Base):
    __tablename__ = 'custom_paper_podcast'
    # doi serves as both primary key and a foreign key to Papers
    doi = Column(String, ForeignKey('papers.doi'), primary_key=True)
    summary = Column(Text, nullable=False)
    podcast_url = Column(String, nullable=False)

    paper = relationship("Paper", backref="custom_podcast")

    def __repr__(self):
        return f"<CustomPaperPodcast(doi='{self.doi}')>"


# ----------------------
# Database Utility Functions
# ----------------------

def create_database(db_url='sqlite:///research.db'):
    """
    Connects to the database, creates all tables, and returns the engine.
    """
    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(engine)
    print("Database and tables created successfully.")
    return engine


def process_new_paper_upload(session, paper_data):
    """
    Processes a new paper upload by checking for duplicate DOI in the Papers table.
    
    If a paper with the given DOI already exists, it will skip reprocessing.
    
    :param session: SQLAlchemy session object.
    :param paper_data: Dictionary containing paper details:
                       {'doi': ..., 'title': ..., 'authors': ..., 'source': ..., 'data': ..., 'summary': ...}
    :return: The new Paper instance if processed, or the existing one if duplicate.
    """
    existing_paper = session.query(Paper).filter_by(doi=paper_data['doi']).first()
    if existing_paper:
        print(f"Paper with DOI {paper_data['doi']} already exists. Skipping processing.")
        return existing_paper
    else:
        new_paper = Paper(**paper_data)
        session.add(new_paper)
        session.commit()
        print(f"Processed new paper with DOI {paper_data['doi']}.")
        return new_paper


def insert_sample_data(session):
    """
    Inserts sample data into all tables for testing purposes.
    """
    # --- Sample Users ---
    users = [
        User(email="alice@example.com", hashed_password="hash_alice", preferences={"theme": "dark", "notifications": True}),
        User(email="bob@example.com", hashed_password="hash_bob", preferences={"theme": "light", "notifications": False}),
        User(email="carol@example.com", hashed_password="hash_carol", preferences={"theme": "dark", "notifications": True}),
    ]
    session.add_all(users)
    session.commit()

    # --- Sample Papers ---
    papers = [
        Paper(doi="10.1000/xyz123", title="Research Paper 1", authors="Author A, Author B", source="Journal X", data="Data content 1", summary="Summary of paper 1"),
        Paper(doi="10.1000/xyz124", title="Research Paper 2", authors="Author C", source="Journal Y", data="Data content 2", summary="Summary of paper 2"),
        Paper(doi="10.1000/xyz125", title="Research Paper 3", authors="Author D, Author E", source="Journal Z", data="Data content 3", summary="Summary of paper 3"),
        Paper(doi="10.1000/xyz126", title="Research Paper 4", authors="Author F", source="Journal W", data="Data content 4", summary="Summary of paper 4"),
        Paper(doi="10.1000/xyz127", title="Research Paper 5", authors="Author G, Author H", source="Journal V", data="Data content 5", summary="Summary of paper 5"),
    ]
    session.add_all(papers)
    session.commit()

    # --- Sample Newsletters ---
    newsletters = [
        Newsletter(title="Newsletter Title 1", date=datetime.datetime(2025, 1, 15), picture="picture1.png", content="Content of newsletter 1", description="A brief description for newsletter 1"),
        Newsletter(title="Newsletter Title 2", date=datetime.datetime(2025, 1, 22), picture="picture2.png", content="Content of newsletter 2", description="A brief description for newsletter 2"),
        Newsletter(title="Newsletter Title 3", date=datetime.datetime(2025, 2, 22), picture="picture3.png", content="Content of newsletter 3", description="A brief description for newsletter 3"),
        Newsletter(title="Newsletter Title 4", date=datetime.datetime(2025, 3, 22), picture="picture4.png", content="Content of newsletter 4", description="A brief description for newsletter 4"),
    ]
    session.add_all(newsletters)
    session.commit()

    # --- Sample UserUploads ---
    user_uploads = [
        UserUpload(user_id=users[0].user_id, doi="10.1000/xyz128", original_pdf="upload1.pdf", summary="User summary 1"),
        UserUpload(user_id=users[1].user_id, doi="10.1000/xyz129", original_pdf="upload2.pdf", summary="User summary 2"),
        UserUpload(user_id=users[2].user_id, doi="10.1000/xyz130", original_pdf="upload3.pdf", summary="User summary 3"),
    ]
    session.add_all(user_uploads)
    session.commit()

    # --- Sample Chats ---
    chats = [
        Chat(user_id=users[0].user_id, paper_doi="10.1000/xyz123", messages={"conversation": ["Hello", "How can I help?"]}),
        Chat(user_id=users[1].user_id, summary_id=newsletters[0].summary_id, messages={"conversation": ["What's new?", "Newsletter update!"]}),
    ]
    session.add_all(chats)
    session.commit()

    # --- Sample NewsletterPodcasts ---
    newsletter_podcasts = [
        NewsletterPodcast(summary_id=newsletters[0].summary_id, content="Podcast content for newsletter 1", podcast_url="http://example.com/podcast1.mp3"),
        NewsletterPodcast(summary_id=newsletters[1].summary_id, content="Podcast content for newsletter 2", podcast_url="http://example.com/podcast2.mp3"),
    ]
    session.add_all(newsletter_podcasts)
    session.commit()

    # --- Sample CustomPaperPodcasts ---
    custom_paper_podcasts = [
        CustomPaperPodcast(doi="10.1000/xyz123", summary="Podcast summary for paper 1", podcast_url="http://example.com/custompodcast1.mp3"),
        CustomPaperPodcast(doi="10.1000/xyz124", summary="Podcast summary for paper 2", podcast_url="http://example.com/custompodcast2.mp3"),
        CustomPaperPodcast(doi="10.1000/xyz125", summary="Podcast summary for paper 3", podcast_url="http://example.com/custompodcast3.mp3"),
    ]
    session.add_all(custom_paper_podcasts)
    session.commit()

    print("Sample data inserted successfully.")


# ----------------------
# Main Execution
# ----------------------

if __name__ == '__main__':
    # Create the database and tables
    engine = create_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Insert sample data into the database
    insert_sample_data(session)

    # --- Demonstrate processing a new paper upload ---
    new_paper_data = {
        "doi": "10.1000/xyz131",
        "title": "New Research Paper",
        "authors": "Author I, Author J",
        "source": "Journal New",
        "data": "New data content",
        "summary": "Summary of the new research paper"
    }
    process_new_paper_upload(session, new_paper_data)

    # Attempt to process a duplicate paper upload (should skip processing)
    duplicate_paper_data = {
        "doi": "10.1000/xyz123",  # Already exists in sample data
        "title": "Duplicate Research Paper",
        "authors": "Author A, Author B",
        "source": "Journal X",
        "data": "Data content duplicate",
        "summary": "Duplicate summary"
    }
    process_new_paper_upload(session, duplicate_paper_data)
