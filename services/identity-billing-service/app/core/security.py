# /identity-billing-service/app/core/security.py
import os
import sys
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

internal_api_key_header = APIKeyHeader(name="X-Internal-Token", auto_error=True)

token_bearer = HTTPBearer()

def verify_internal_token(api_key: str = Security(internal_api_key_header)):
    """
    Used exclusively to authenticate requests coming from other internal 
    microservices (like the payment-worker) bypassing JWTs.
    """
    if api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid internal communication token"
        )
    return True

# --- Keycloak JWT Validation ---

# In production, pull this from your config/environment variables.
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL")

print(f"--- DEBUG: OIDC_ISSUER_URL is set to: '{OIDC_ISSUER_URL}'", file=sys.stdout)

if not OIDC_ISSUER_URL:
    raise RuntimeError("OIDC_ISSUER_URL is missing!")

KEYCLOAK_CERTS_URL = f"{OIDC_ISSUER_URL}/protocol/openid-connect/certs"
print(f"--- DEBUG: Constructing JWKS URL as: '{KEYCLOAK_CERTS_URL}'", file=sys.stdout)
# PyJWKClient fetches and caches the public keys from Keycloak
jwks_client = PyJWKClient(KEYCLOAK_CERTS_URL)


async def verify_and_decode_jwt(credentials: HTTPAuthorizationCredentials = Security(token_bearer)):
    """
    Used exclusively by the Identity Service's /verify endpoint to 
    validate the Keycloak token and extract user details for JIT provisioning.
    """
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                "verify_aud": False
            }
        )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject (sub)."
            )

        # Return the full payload so JIT provisioning can grab the email/username
        return payload

    except jwt.ExpiredSignatureError:
        print("--- DEBUG: Token rejected because it is EXPIRED ---")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"--- DEBUG: Token rejected! Reason: {str(e)} ---")
        raise HTTPException(status_code=401, detail="Invalid token payload or signature")
    except Exception as e:
        import traceback
        print("--- CRASH DEBUG START ---")
        traceback.print_exc()
        print("--- CRASH DEBUG END ---")
        raise HTTPException(status_code=500, detail="Internal identity verification error")

# --- Standard Dependency for Protected Routes ---
async def get_current_user_id(x_user_id: str = Header(None, alias="X-User-ID")):
    """
    Used by all microservices to get the user ID injected by the API Gateway.
    Bypasses token decoding entirely.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing identity context"
        )
    return x_user_id