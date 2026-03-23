# /payment-worker/worker.py
import json
import stripe
import httpx
from arq.connections import RedisSettings
import asyncio
import arq

from config import settings

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
# --- 1. Verification Helpers ---

async def verify_stripe(raw_payload: bytes, headers: dict) -> dict | None:
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ValueError("Stripe secret not configured")

    sig_header = headers.get("stripe-signature")
    if not sig_header:
        raise ValueError("Missing Stripe signature")

    # Verify signature
    event = stripe.Webhook.construct_event(
        payload=raw_payload, 
        sig_header=sig_header, 
        secret=settings.STRIPE_WEBHOOK_SECRET
    )

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        return {
            "user_id": session.get('client_reference_id'),
            "package_id": session.get('metadata', {}).get('package_id')
        }
    return None

async def verify_paypal(raw_payload: bytes, headers: dict) -> dict | None:
    """Uses httpx for async PayPal verification API calls."""
    if not settings.PAYPAL_WEBHOOK_ID:
        raise ValueError("PayPal webhook ID not configured")

    base_url = "https://api-m.paypal.com" if settings.PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"
    
    # Get Access Token asynchronously
    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            f"{base_url}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"}
        )
        auth_response.raise_for_status()
        access_token = auth_response.json()['access_token']

        # Verify Signature asynchronously
        headers_lower = {k.lower(): v for k, v in headers.items()}
        verification_payload = {
            "auth_algo": headers_lower.get("paypal-auth-algo"),
            "cert_url": headers_lower.get("paypal-cert-url"),
            "transmission_id": headers_lower.get("paypal-transmission-id"),
            "transmission_sig": headers_lower.get("paypal-transmission-sig"),
            "transmission_time": headers_lower.get("paypal-transmission-time"),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": json.loads(raw_payload.decode("utf-8"))
        }

        verify_req = await client.post(
            f"{base_url}/v1/notifications/verify-webhook-signature",
            headers={"Authorization": f"Bearer {access_token}"},
            json=verification_payload
        )
        verify_req.raise_for_status()
        
        if verify_req.json().get("verification_status") != "SUCCESS":
            raise ValueError("PayPal signature verification failed")

    # If verified, parse payload
    event = json.loads(raw_payload.decode("utf-8"))
    if event.get('event_type') == "CHECKOUT.ORDER.APPROVED":
        purchase_unit = event.get('resource', {}).get('purchase_units', [{}])[0]
        return {
            "user_id": purchase_unit.get('custom_id'),
            "package_id": purchase_unit.get('reference_id')
        }
    return None

# --- 2. The Main ARQ Job ---

async def process_webhook_job(ctx, provider_name: str, raw_payload: bytes, headers: dict):
    print(f"Worker picked up {provider_name} webhook...")
    
    try:
        # 1. Verify and Extract
        extracted_data = None
        if provider_name == "stripe":
            extracted_data = await verify_stripe(raw_payload, headers)
        elif provider_name == "paypal":
            extracted_data = await verify_paypal(raw_payload, headers)
        else:
            print(f"Unknown provider: {provider_name}")
            return
            
        if not extracted_data or not extracted_data.get("user_id"):
            print("Webhook ignored (Not a completed payment or missing user data)")
            return

        print(f"Verified payment for User {extracted_data['user_id']}. Handing off to Identity Service...")

        # 2. Secure Handoff to Identity Service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.IDENTITY_API_URL}/internal/add-credits",
                json={
                    "user_id": extracted_data["user_id"],
                    "package_id": extracted_data["package_id"]
                },
                headers={"X-Internal-Token": settings.INTERNAL_API_KEY}
            )
            response.raise_for_status()
            
        print("Handoff successful.")
        return True

    except Exception as e:
        print(f"Worker failed to process webhook: {e}")
        # Raising the exception tells ARQ to retry the job later
        raise e

# --- 3. ARQ Configuration ---

class WorkerSettings:
    functions = [process_webhook_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_tries = 3 # Retries 3 times if the Identity Service is temporarily down