# /identity-billing-service/app/api/routers/internal.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_internal_token
from app.repositories.user_repo import UserRepository
from app.core.packages import CREDIT_PACKAGES

# Notice we apply the dependency to the ENTIRE router
router = APIRouter(tags=["Internal"], dependencies=[Depends(verify_internal_token)])

class AddCreditsRequest(BaseModel):
    user_id: str
    package_id: str

@router.post("/add-credits")
async def internal_add_credits(request: AddCreditsRequest, db: AsyncSession = Depends(get_db)):
    package = CREDIT_PACKAGES.get(request.package_id)
    if not package:
        raise HTTPException(status_code=400, detail="Invalid package ID")
        
    repo = UserRepository(db)
    
    # Await the DB call (using the async pattern we set up earlier)
    updated_user = await repo.add_credits(request.user_id, package["credits"])
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"message": "Credits added successfully", "new_balance": updated_user.credits}