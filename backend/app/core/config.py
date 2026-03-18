# /backend/app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "CraftCloud API"
    DOMAIN_URL: str = "http://localhost:3000"  # Default frontend URL

    # Database
    DATABASE_URL: str

    # Infrastructure (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change_this_to_a_secure_random_string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Payments (Stripe & PayPal)
    STRIPE_SECRET_KEY: str | None = None
    PAYPAL_CLIENT_ID: str | None = None
    PAYPAL_CLIENT_SECRET: str | None = None
    PAYPAL_MODE: str = "sandbox"  # 'sandbox' or 'live'

    class Config:
        # This tells Pydantic to read your .env file
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()