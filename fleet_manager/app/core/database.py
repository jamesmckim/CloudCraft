# /app/core/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite for local testing if no URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fleet_manager.db")

# SQLite requires specific connect args to avoid thread issues; Postgres does not
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI Routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()