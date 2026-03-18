# backend/app/api/routers/payments.py
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Database / Dependencies
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.payment_service import PaymentService
from app.core.security import get_current_user_id

router = APIRouter(tags=["Payments"])

# --- Dependency Injection Helper ---
def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    # 1. Create the Repo
    user_repo = UserRepository(db)
    # 2. Inject Repo into Service
    return PaymentService(user_repo)

# --- Request Models ---
class BuyRequest(BaseModel):
    package_id: str
    provider: str  # 'stripe' or 'paypal'

# --- Routes ---

@router.post("/checkout")
async def create_checkout(
    request: BuyRequest, 
    service: PaymentService = Depends(get_payment_service),
    current_user_id = Depends(get_current_user_id)
):
    """
    Creates a payment session url (Stripe or PayPal)
    """
    # Delegate logic to the service
    return service.checkout(
        user_id=current_user_id,
        package_id=request.package_id,
        provider_name=request.provider
    )

@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: str, 
    request: Request, 
    service: PaymentService = Depends(get_payment_service)
):
    """
    Unified webhook endpoint for Stripe and PayPal
    """
    try:
        # We need the raw JSON for verification
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Delegate logic to the service
    return service.process_webhook(provider, payload)