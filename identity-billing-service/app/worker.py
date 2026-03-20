# /identity-billing-service/app/worker.py
import asyncio
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.user_repo import UserRepository
from app.services.payment_service import PaymentService

async def process_webhook_job(ctx, provider_name: str, raw_payload: bytes, headers: dict):
    """
    This function is executed by the ARQ worker pod. 
    It runs outside the API's event loop.
    """
    print(f"Worker picked up {provider_name} webhook...")
    
    # 1. Create a fresh database session for this specific background job
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        payment_service = PaymentService(user_repo)
        
        # 2. Execute the verification and database logic
        # (Assuming you already converted process_webhook to an async function)
        result = await payment_service.process_webhook(provider_name, raw_payload, headers)
        
        print(f"Worker finished processing: {result}")
        return result

# ARQ expects a WorkerSettings class to configure its behavior
class WorkerSettings:
    functions = [process_webhook_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    
    # Optional: Automatically retry failed jobs if the DB is temporarily down
    max_tries = 3