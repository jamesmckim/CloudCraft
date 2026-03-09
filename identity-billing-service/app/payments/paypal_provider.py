# /backend/app/payments/paypal_provider.py
import requests
import os
import base64

from app.payments.driver import PaymentProvider
from app.core.packages import CREDIT_PACKAGES

class PayPalProvider(PaymentProvider):
    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.domain = os.getenv("DOMAIN_URL")

        # Check environment to switch between Sandbox and Live
        # Ideally, set PAYPAL_MODE='live' in your .env for production
        if os.getenv("PAYPAL_MODE") == "live":
            self.base_url = "https://api-m.paypal.com"
        else:
            self.base_url = "https://api-m.sandbox.paypal.com"

    def _get_access_token(self):
        """
        Generates a temporary OAuth 2.0 access token using Client Credentials.
        """
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(
                url, 
                auth=(self.client_id, self.client_secret), 
                headers=headers, 
                data=data
            )
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            print(f"PayPal Auth Failed: {e}")
            raise Exception("Could not authenticate with PayPal")

    def create_checkout_session(self, package_id, user_id):
        package = CREDIT_PACKAGES.get(package_id)
        if not package:
            raise ValueError(f"Package {package_id} not found")

        # 1. Get a fresh access token
        access_token = self._get_access_token()

        # 2. Prepare the Order Payload
        url = f"{self.base_url}/v2/checkout/orders"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": package_id, # Our internal Package ID
                "custom_id": user_id,       # Our internal User ID
                "amount": {
                    "currency_code": "USD",
                    "value": str(package['price_usd'])
                }
            }],
            "application_context": {
                "return_url": f"{self.domain}/dashboard?success=true",
                "cancel_url": f"{self.domain}/dashboard?canceled=true",
                "user_action": "PAY_NOW"  # Changes the button text to 'Pay Now'
            }
        }

        # 3. Send Request
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            if response.status_code not in [200, 201]:
                print(f"PayPal Order Error: {response_data}")
                raise Exception("PayPal creation failed: API Error")

            # 4. Extract the 'approve' link (redirect URL)
            for link in response_data.get('links', []):
                if link['rel'] == "approve":
                    return {"url": link['href']}

            raise Exception("No approval URL found in PayPal response")

        except Exception as e:
            print(f"PayPal Exception: {e}")
            raise Exception("PayPal creation failed")
    def verify_webhook(self, request_data: dict):
        """
        1. Checks if the event is CHECKOUT.ORDER.APPROVED
        2. Captures the payment (Moves the money)
        3. Returns the user and credit info
        """
        event_type = request_data.get('event_type')

        # We only care when the user has approved the payment
        if event_type == "CHECKOUT.ORDER.APPROVED":
            resource = request_data.get('resource', {})
            order_id = resource.get('id')

            # 1. Capture the payment (Critical Step!)
            try:
                capture_details = self._capture_order(order_id)
            except Exception as e:
                print(f"Capture Failed: {e}")
                return None

            # 2. Extract User and Package info from the webhook payload
            # (We stored these in purchase_units during create_checkout_session)
            purchase_unit = resource.get('purchase_units', [{}])[0]
            user_id = purchase_unit.get('custom_id')
            package_id = purchase_unit.get('reference_id')

            package = CREDIT_PACKAGES.get(package_id)

            if user_id and package:
                return {
                    "user_id": user_id,
                    "credits": package['credits'],
                    "status": "paid"
                }

        return None

    def _capture_order(self, order_id):
        """
        Helper to finalize the transaction.
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.post(url, headers=headers)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to capture order: {response.text}")

        return response.json()
