# /identity-billing-service/app/services/auth_service.py
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.repositories.user_repo import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def sync_idp_user(self, keycloak_id: str, email: str, username: str) -> User:
        
        existing_user = await self.user_repo.get_by_id(keycloak_id)

        if existing_user:
            return existing_user

        new_user = User(
            id=keycloak_id,
            username=username or f"user_{keycloak_id[:8]}",
            email=email,
            credits=0
        )

        try:
            await self.user_repo.create(new_user) 
            return new_user
        except SQLAlchemyError:
            await self.user_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during registration"
            )