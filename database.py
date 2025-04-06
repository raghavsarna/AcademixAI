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
    from models import User, Newsletter

    # Drop all tables first to ensure a clean start
    Base.metadata.drop_all(bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)