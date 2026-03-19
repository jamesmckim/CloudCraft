# /identity-billing-service/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Identity & Billing API"
    DOMAIN_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Payments (Stripe & PayPal)
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    PAYPAL_CLIENT_ID: str | None = None
    PAYPAL_CLIENT_SECRET: str | None = None
    PAYPAL_WEBHOOK_ID: str | None = None
    PAYPAL_MODE: str = "sandbox"  # 'sandbox' or 'live'

    model_config = SettingsConfigDict(
        env_file = ".env",
        case_sensitive = True,
        extra = "ignore"
    )

settings = Settings()