# /telemetry-service/app/api/dependencies.py
import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.incident_repo import IncidentRepository
from app.services.incident_service import IncidentService
from app.services.telemetry_service import TelemetryService

# Global instances for the Singleton pattern
_redis_client: aioredis.Redis | None = None
_arq_pool: ArqRedis | None = None

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True
        )
    return _redis_client

async def get_arq_pool() -> ArqRedis:
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings(
            host=settings.REDIS_HOST, # Uses the clean config variables
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD
        ))
    return _arq_pool

def get_incident_service(
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool)
) -> IncidentService:
    repo = IncidentRepository(db)
    return IncidentService(repo, arq_pool)

def get_telemetry_service(
    redis: aioredis.Redis = Depends(get_redis),
    arq_pool: ArqRedis = Depends(get_arq_pool)
) -> TelemetryService:
    return TelemetryService(redis, arq_pool)