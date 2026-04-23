# /telemetry-service/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database & Redis
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis-broker-master:6379/0"
    REDIS_PASSWORD: str | None = None
    
    # Auth & Security
    SECRET_KEY: str
    SIDECAR_API_KEY: str
    
    # Telemetry logic
    AI_COOLDOWN_SECONDS: int = 120
    MAX_BUFFER_LINES: int = 50

    model_config = SettingsConfigDict(
        case_sensitive = True,
        env_file=".env",
        extr="ignore"
    )

settings = Settings()