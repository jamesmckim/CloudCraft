# /telemetry-service/app/core/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    PROJECT_NAME: str = "Telemetry"
    DOMAIN_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str
    
    @field_validator("DATABASE_URL")
    @classmethod
    def format_async_db_url(cls, v: str) -> str:
        """Intercepts the Operator's URL and injects the async driver."""
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis
    REDIS_HOST: str = "redis-broker-master"
    REDIS_PORT: int = 6379
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
        extra="ignore"
    )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        
settings = Settings()