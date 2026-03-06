# /app/api/dependencies.py
import os
from fastapi import Depends
from sqlalchemy.orm import Session
from redis import Redis
from celery import Celery

from app.core.database import SessionLocal
from app.repositories.incident_repo import IncidentRepository
from app.services.incident_service import IncidentService
from app.services.telemetry_service import TelemetryService

# Global connection instances
redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
celery_app = Celery("telemetry_tasks", broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"), backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> Redis:
    return redis_client

def get_celery() -> Celery:
    return celery_app

def get_incident_service(db: Session = Depends(get_db), celery: Celery = Depends(get_celery)) -> IncidentService:
    repo = IncidentRepository(db)
    return IncidentService(repo, celery)

def get_telemetry_service(redis: Redis = Depends(get_redis), celery: Celery = Depends(get_celery)) -> TelemetryService:
    return TelemetryService(redis, celery)