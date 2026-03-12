# /fleet-manager/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fleet Manager API"
    
    # K8s Internal Service Discovery
    # Defaults to the Service names we found in your 'kubectl get pods'
    IDENTITY_SERVICE_URL: str = "http://identity-service:5000"
    MANAGER_API_URL: str = "http://fleet-service:5000"
    
    REDIS_HOST: str = "redis-broker"
    REDIS_PORT: int = 6379

    # Database & Security
    DATABASE_URL: str
    
    NAMESPACE: str = "default"
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        case_sensitive = True,
        extra = "ignore"
    )

settings = Settings()