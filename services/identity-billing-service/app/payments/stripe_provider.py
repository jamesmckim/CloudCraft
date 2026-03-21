# /identity-billing-service/app/payments/stripe_provider.py
import stripe
import os

from app.payments.driver import PaymentProvider
from app.core.packages import CREDIT_PACKAGES

class StripeProvider(PaymentProvider):
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.domain = os.getenv("DOMAIN_URL")

    def create_checkout_session(self, package_id, user_id):
        package = CREDIT_PACKAGES.get(package_id)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': package['stripe_price_id'], 'quantity': 1}],
            mode='payment',
            success_url=self.domain + '/dashboard?success=true',
            cancel_url=self.domain + '/dashboard?canceled=true',
            client_reference_id=user_id,
            metadata={"package_id": package_id}
        )
        return {"url": session.url}
        
    def verify_webhook(self, raw_payload: bytes, headers: dict):
        if not self.webhook_secret:
            raise Exception("Stripe webhook secret is not configured.")

        sig_header = headers.get("stripe-signature")
        
        if not sig_header:
            raise Exception("Missing Stripe signature header")

        try:
            event = stripe.Webhook.construct_event(
                payload=raw_payload, 
                sig_header=sig_header, 
                secret=self.webhook_secret
            )
        except ValueError as e:
            raise Exception("Invalid payload") from e
        except stripe.error.SignatureVerificationError as e:
            raise Exception("Invalid signature") from e

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            user_id = session.get('client_reference_id')
            package_id = session.get('metadata', {}).get('package_id')
            
            package = CREDIT_PACKAGES.get(package_id)

            if user_id and package:
                return {
                    "user_id": user_id,
                    "credits": package['credits'],
                    "status": "paid"
                }
        
        return None