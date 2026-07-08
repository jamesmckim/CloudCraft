# /identity-billing-service/app/api/routers/auth.py
from fastapi import APIRouter, Depends, status, Response

from app.core.database import get_db
from app.core.security import verify_and_decode_jwt
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)

@router.get("/verify")
async def verify_token(
    response: Response,
    token_payload: dict = Depends(verify_and_decode_jwt),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Called by Traefik ForwardAuth. 
    Validates the Keycloak JWT, provisions the user if they are new, 
    and returns the X-User-ID header for internal microservice routing.
    """
    user_id = token_payload.get("sub")
    
    # Just-In-Time Provisioning: Sync Keycloak user to local DB for billing tracking
    await auth_service.sync_idp_user(
        keycloak_id=user_id, 
        email=token_payload.get("email"), 
        username=token_payload.get("preferred_username")
    )

    # Traefik ForwardAuth expects a 20X response to allow traffic through
    response.status_code = status.HTTP_200_OK
    
    # Inject the validated user ID into the header for Traefik to extract and pass downstream
    response.headers["X-User-ID"] = str(user_id)
    
    return {"status": "authenticated"}