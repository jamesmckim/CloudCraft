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

# Global connection instances
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis() -> aioredis.Redis:
    return redis_client

async def get_arq_pool() -> ArqRedis:
    return await create_pool(RedisSettings(
        host="redis-broker-master",
        port=6379,
        password=settings.REDIS_PASSWORD
        )

def get_incident_service(db: AsyncSession = Depends(get_db), arq_pool: ArqRedis = Depends(get_arq_pool)) -> IncidentService:
    repo = IncidentRepository(db)
    return IncidentService(repo, arq_pool)

def get_telemetry_service(redis: aioredis.Redis = Depends(get_redis), arq_pool: ArqRedis = Depends(get_arq_pool)) -> TelemetryService:
    return TelemetryService(redis, arq_pool)