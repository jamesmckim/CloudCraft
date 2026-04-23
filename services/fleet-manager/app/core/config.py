# /fleet-manager/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fleet Manager API"
    
    # K8s Internal Service Discovery
    IDENTITY_SERVICE_URL: str = "http://identity-service:5000"
    MANAGER_API_URL: str = "http://fleet-service:5000"
    TELEMETRY_API_URL: str = "http://telemetry-service.craftcloud-system.svc.cluster.local:5000"
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis-broker-master")
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    # Database & Security
    DATABASE_URL: str
    
    NAMESPACE: str = "valheim-workloads"
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        case_sensitive = True,
        extra = "ignore"
    )

settings = Settings()