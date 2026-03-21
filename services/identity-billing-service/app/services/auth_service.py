# /identity-billing-service/app/services/auth_service.py
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user_schemas import UserRegister
from app.models.user import User
from app.repositories.user_repo import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_data: UserRegister) -> User:
        
        existing_user = await self.user_repo.get_by_username(
            user_data.username, user_data.email
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or Email already registered"
            )

        hashed_pw = await run_in_threadpool(get_password_hash(user_data.password))

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw,
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

    async def authenticate_user(self, username: str, password: str) -> dict:
        user = await self.user_repo.get_by_username(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password"
            )

        is_password_valid = await run_in_threadpool(
            verify_password, password, user.hashed_password
        )

        if not is_password_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password"
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}