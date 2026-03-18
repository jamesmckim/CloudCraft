# /backend/app/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from redis import Redis
from celery import Celery
import os

# Import your database session factory
from app.core.database import get_db 

# Import the new components
from app.core.manager import ServerManager
from app.repositories.user_repo import UserRepository
from app.repositories.incident_repo import IncidentRepository
from app.repositories.server_repo import ServerRepository
from app.services.server_service import ServerService
from app.services.incident_service import IncidentService
from app.services.telemetry_service import TelemetryService

from app.config.reader import GAME_TEMPLATES, SETTINGS

# --- Configuration ---
# We standardize the connection details here so both Redis and Celery use the same config
from app.core.config import settings

# Global Singletons (Initialized once)
# In a real app, you might want to initialize these in a lifespan event or strictly inside the dependency
_server_manager = ServerManager(GAME_TEMPLATES, SETTINGS)
_redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True # Helper to get strings back instead of bytes
)

_celery_sender = Celery("manager_api", broker=settings.REDIS_URL)

def get_server_manager() -> ServerManager:
    return _server_manager

def get_redis() -> Redis:
    return _redis_client

def get_celery_sender() -> Celery:
    return _celery_sender

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_server_repo(db: Session = Depends(get_db)) -> ServerRepository:
    return ServerRepository(db)

def get_incident_repo(db: Session = Depends(get_db)) -> IncidentRepository:
    return IncidentRepository(db)

def get_server_service(
    user_repo: UserRepository = Depends(get_user_repo),
    server_repo: ServerRepository = Depends(get_server_repo),
    manager: ServerManager = Depends(get_server_manager),
    redis: Redis = Depends(get_redis)
) -> ServerService:
    """
    Injects the Repo, Manager, and Redis into the Service.
    This is what your Router/Controller will depend on.
    """
    return ServerService(
        user_repo=user_repo,
        server_repo=server_repo,
        manager=manager,
        redis=redis)

def get_incident_service(
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    celery: Celery = Depends(get_celery_sender)
) -> IncidentService:
    return IncidentService(incident_repo=incident_repo, celery_app=celery)

def get_telemetry_service(
    redis: Redis = Depends(get_redis),
    celery: Celery = Depends(get_celery_sender)
) -> TelemetryService:
    return TelemetryService(redis_client=redis, celery_app=celery)