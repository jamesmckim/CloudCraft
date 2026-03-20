# /identity-billing-service/app/services/payment_service.py
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.repositories.user_repo import UserRepository
from app.payments.stripe_provider import StripeProvider
from app.payments.paypal_provider import PayPalProvider
from app.core.packages import CREDIT_PACKAGES

class PaymentService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.providers = {
            "stripe": StripeProvider(),
            "paypal": PayPalProvider()
        }

    async def checkout(self, user_id: str, package_id: str, provider_name: str):
        if package_id not in CREDIT_PACKAGES:
            raise HTTPException(status_code=400, detail=f"Invalid package_id: {package_id}")

        provider = self.providers.get(provider_name)
        if not provider:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider_name}")

        return await run_in_threadpool(
            provider.create_checkout_session(package_id, str(user_id))
        )

    async def process_webhook(self, provider_name: str, raw_payload: bytes, headers: dict):
        provider = self.providers.get(provider_name)
        if not provider:
            print(f"Webhook Error: Unknown provider {provider_name}")
            return {"status": "ignored", "reason": "Unknown provider"}

        try:
            result = await run_in_threadpool(
                provider.verify_webhook(raw_payload, headers)
            )
        except Exception as e:
            print(f"Webhook Verification Failed: {e}")
            return {"status": "failed", "error": str(e)}

        if result and result.get("status") == "paid":
            user_id = result["user_id"]
            credits_to_add = result["credits"]

            print(f"Payment Verified! Adding {credits_to_add} credits to User {user_id}")
            await self.user_repo.add_credits(user_id, credits_to_add)
            
            return {"status": "success"}

        return {"status": "ignored"}