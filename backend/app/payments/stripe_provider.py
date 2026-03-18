# /backend/app/payments/stripe_provider.py
import stripe
import os

from app.payments.driver import PaymentProvider
from app.core.packages import CREDIT_PACKAGES

class StripeProvider(PaymentProvider):
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
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
            metadata={"package_id": package_id} # Store the ID so we know what they bought
        )
        return {"url": session.url}