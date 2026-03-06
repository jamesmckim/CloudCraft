# /app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database & Redis
    DATABASE_URL: str
    REDIS_URL: str = "redis://telemetry-redis:6379/0"
    CELERY_BROKER_URL: str = "redis://telemetry-redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://telemetry-redis:6379/2"
    
    # Auth & Security
    JWT_SECRET: str
    SIDECAR_API_KEY: str
    
    # Telemetry logic
    AI_COOLDOWN_SECONDS: int = 120
    MAX_BUFFER_LINES: int = 50

    class Config:
        case_sensitive = True

settings = Settings()