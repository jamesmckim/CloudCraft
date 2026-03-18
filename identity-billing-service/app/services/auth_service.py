# /identity-billing-service/app/services/auth_service.py
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user_schemas import UserRegister
from app.models.user import User
from app.repositories.user_repo import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, user_data: UserRegister) -> User:
        if self.user_repo.get_by_username_or_email(user_data.username, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or Email already registered"
            )

        hashed_pw = get_password_hash(user_data.password)

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw,
            credits=0
        )

        try:
            self.user_repo.create(new_user) 
            return new_user
        except SQLAlchemyError:
            self.user_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during registration"
            )

    def authenticate_user(self, username: str, password: str) -> dict:
        user = self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password"
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}