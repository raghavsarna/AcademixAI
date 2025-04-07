from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Ensure the db directory exists
os.makedirs("db", exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///db/research.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Create tables
def create_tables():
    # Import models here to avoid circular imports
    # This ensures models are imported only when create_tables is called
    # These imports are necessary for SQLAlchemy to discover the models and create tables
    # pylint: disable=unused-import
    from models import User, Newsletter, Research, Paper, UserUpload, Chat, NewsletterPodcast, CustomPaperPodcast

    # In a production environment, you might want to comment out the next line
    # to avoid dropping tables accidentally
    # Base.metadata.drop_all(bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)