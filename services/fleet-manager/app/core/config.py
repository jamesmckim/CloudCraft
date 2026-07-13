# /fleet-manager/app/core/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fleet Manager API"
    DOMAIN_URL: str = "http://localhost:3000"

    # Database
    NAMESPACE: str = "valheim-workloads"
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

    # K8s Internal Service Discovery
    IDENTITY_SERVICE_URL: str = "http://identity-service:5000"
    MANAGER_API_URL: str = "http://fleet-service:5000"
    TELEMETRY_API_URL: str = "http://telemetry-service:5000"
    
    REDIS_HOST: str = "redis-broker-master"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        case_sensitive = True,
        extra = "ignore"
    )
    
    @property
    def redis_url(self) -> str:
        """Safely constructs the Redis DSN."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

settings = Settings()