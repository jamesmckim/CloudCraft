# /identity-billing-service/app/api/routers/payments.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user_schemas import BuyRequest
from app.repositories.user_repo import UserRepository
from app.services.payment_service import PaymentService
from app.core.security import get_current_user_id

router = APIRouter(tags=["Payments"])

def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    user_repo = UserRepository(db)
    return PaymentService(user_repo)

@router.post("/checkout")
async def create_checkout(
    request: BuyRequest, 
    service: PaymentService = Depends(get_payment_service),
    current_user_id = Depends(get_current_user_id)
):
    return await service.checkout(
        user_id=current_user_id,
        package_id=request.package_id,
        provider_name=request.provider
    )

@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: str, 
    request: Request
):
    raw_payload = await request.body()
    headers = dict(request.headers)
    
    redis = request.app.state.redis
    await redis.equeue_job(
        "process_webhook_job",
        provider,
        raw_payload,
        headers
    )
    
    return {"status": "queued"}