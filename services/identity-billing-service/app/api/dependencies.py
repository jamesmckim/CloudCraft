# /identity-billing-service/app/api/dependencies.py
from fastapi import Depends
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from app.core.config import settings

# Singleton instance
_arq_pool: ArqRedis | None = None

async def get_arq_pool() -> ArqRedis:
    """Returns a shared arq connection pool, creating it if necessary."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD
        ))
    return _arq_pool