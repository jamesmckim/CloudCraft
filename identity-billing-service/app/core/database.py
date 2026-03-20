# /identity-billing-service/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
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
    """Creates tables if they don't exist"""
    # Updated import to point exclusively to the isolated User model
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)