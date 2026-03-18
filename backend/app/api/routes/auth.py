# /backend/app/api/routes/authRoutes.py
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Custom Imports
from app.dependencies import get_db
from app.schemas.schemas import UserRegister, UserProfile
from app.core.security import get_current_user_id
from app.models.models import User

# Service Layer Imports
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])

# --- Dependency Injection Helper ---
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Creates an AuthService instance with a UserRepository.
    This ensures the service has access to the database session.
    """
    repo = UserRepository(db)
    return AuthService(repo)

# --- Routes ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user: UserRegister, 
    service: AuthService = Depends(get_auth_service)
):
    """
    Delegates registration logic to AuthService.
    """
    new_user = service.register_user(user)
    return {"message": "Account created successfully", "user_id": new_user.id}

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """
    Delegates authentication logic to AuthService.
    """
    return service.authenticate_user(form_data.username, form_data.password)

@router.get("/users/me", response_model=UserProfile)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    """
    This route currently remains mostly the same as it primarily
    retrieves data. You could move 'get_user_by_id' to the service
    if you wanted full strictness, but for simple reads, 
    Repo access or direct query is often acceptable.
    """
    # Convert the token's string ID back into an integer for the DB!
    try:
        db_user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format in token")
    
    # Optional: You could use the Repo here for consistency
    repo = UserRepository(db)
    user = repo.get_by_id(db_user_id)
    
    # Fallback to direct query if Repo doesn't have ID lookup yet
    if not user:
        user = db.query(User).filter(User.id == db_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user