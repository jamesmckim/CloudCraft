# /identity-billing-service/app/api/routers/payments.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from app.core.database import get_db
from app.api.dependencies import get_arq_pool
from app.schemas.user_schemas import BuyRequest, CreditGrantRequest
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
    request: Request,
    redis: ArqRedis = Depends(get_arq_pool)
):
    raw_payload = await request.body()
    headers = dict(request.headers)
    
    await redis.enqueue_job(
        "process_webhook_job",
        provider,
        raw_payload,
        headers
    )
    
    return {"status": "queued"}

# needs to be removed
@router.post("/grant")
async def grant_free_credits(
    request: CreditGrantRequest, 
    service: PaymentService = Depends(get_payment_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Directly adds credits to the current user's wallet without external payment processing.
    """
    return await service.grant_credits(
        user_id=current_user_id, 
        amount=request.amount
    )