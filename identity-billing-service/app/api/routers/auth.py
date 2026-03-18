# /identity-billing-service/app/api/routers/auth.py
from fastapi import APIRouter, Depends, status, HTTPException, Header, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user_schemas import UserRegister
from app.core.security import get_current_user_id, verify_and_decode_jwt
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)

@router.get("/verify")
async def verify_token(
    user_id: str = Depends(verify_and_decode_jwt),
    # Inject your JWT validation logic here
):
    """
    Called by Traefik ForwardAuth. 
    Validates the JWT and returns the X-User-ID header for internal routing.
    """
    # Traefik ForwardAuth expects a 2xx response
    response = Response(status_code=status.HTTP_200_OK)
    
    # Inject the validated user ID into the header for Traefik to extract
    response.headers["X-User-ID"] = str(user_id)
    return response

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user: UserRegister, 
    service: AuthService = Depends(get_auth_service)
):
    new_user = service.register_user(user)
    return {"message": "Account created successfully", "user_id": new_user.id}

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    return service.authenticate_user(form_data.username, form_data.password)