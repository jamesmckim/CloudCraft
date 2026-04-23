# /payment-worker/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Redis Queue
    REDIS_PASSWORD: str | None = None
    
    # Target API for internal handoff
    IDENTITY_API_URL: str = "http://identity-service:5000"

    INTERNAL_API_KEY: str
    # Stripe
    STRIPE_WEBHOOK_SECRET: str | None = None

    # PayPal
    PAYPAL_CLIENT_ID: str | None = None
    PAYPAL_CLIENT_SECRET: str | None = None
    PAYPAL_WEBHOOK_ID: str | None = None
    PAYPAL_MODE: str = "sandbox"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()