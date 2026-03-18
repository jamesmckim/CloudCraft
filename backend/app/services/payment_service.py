# /backend/app/services/payment_service.py
from fastapi import HTTPException

from app.repositories.user_repo import UserRepository
from app.payments.stripe_provider import StripeProvider
from app.payments.paypal_provider import PayPalProvider
from app.core.packages import CREDIT_PACKAGES

class PaymentService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        # Initialize providers once and hold them in a dictionary
        self.providers = {
            "stripe": StripeProvider(),
            "paypal": PayPalProvider()
        }

    def checkout(self, user_id: str, package_id: str, provider_name: str):
        """
        Validates the package, selects the provider, and creates a checkout session.
        """
        # 1. Validate Package
        if package_id not in CREDIT_PACKAGES:
            raise HTTPException(status_code=400, detail=f"Invalid package_id: {package_id}")

        # 2. Select Provider
        provider = self.providers.get(provider_name)
        if not provider:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider_name}")

        # 3. Create Session
        # Note: Providers return {"url": "..."}
        return provider.create_checkout_session(package_id, str(user_id))

    def process_webhook(self, provider_name: str, payload: dict):
        """
        Verifies the webhook payload and updates user credits if successful.
        """
        # 1. Select Provider
        provider = self.providers.get(provider_name)
        if not provider:
            # We log this but generally return 200 to Stripe/PayPal so they don't retry
            print(f"Webhook Error: Unknown provider {provider_name}")
            return {"status": "ignored", "reason": "Unknown provider"}

        # 2. Verify Payload
        try:
            # verify_webhook returns: {"user_id": "123", "credits": 500, "status": "paid"} or None
            result = provider.verify_webhook(payload)
        except Exception as e:
            print(f"Webhook Verification Failed: {e}")
            return {"status": "failed", "error": str(e)}

        # 3. Fulfill Order (The "Crucial Step")
        if result and result.get("status") == "paid":
            user_id = result["user_id"]
            credits_to_add = result["credits"]

            print(f"Payment Verified! Adding {credits_to_add} credits to User {user_id}")
            
            # Use the Repo to update the database
            # Ensure your UserRepository has an `add_credits` method implemented!
            self.user_repo.add_credits(user_id, credits_to_add)
            
            return {"status": "success"}

        return {"status": "ignored"}