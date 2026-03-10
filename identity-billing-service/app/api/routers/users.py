# /identity-billing-service/app/api/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user_schemas import UserProfile
from app.core.security import get_current_user_id
from app.repositories.user_repo import UserRepository

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserProfile)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        db_user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format in token")
    
    repo = UserRepository(db)
    user = repo.get_by_id(db_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

@router.get("/{user_id}/credits") # This creates the /users/{user_id}/credits path
async def get_user_credits(
    user_id: int, 
    db: Session = Depends(get_db)
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Ensure your User model or Repo has a 'credits' field
    return {"credits": user.credits}