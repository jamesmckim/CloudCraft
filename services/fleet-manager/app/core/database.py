# /fleet-manager/app/core/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# SQLite requires specific connect args to avoid thread issues; Postgres does not
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_async_engine(DATABASE_URL, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    """Dependency for FastAPI Routes"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
            
async def init_db():
    """Safely builds database tables inside the async event loop."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)