# /backend/app/services/auth_service.py
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

# Import your existing utilities and schemas
from app.core.security import get_password_hash, verify_password, create_access_token # need to rename this file to security.py to remove confusion
from app.schemas.schemas import UserRegister
from app.models.models import User
from app.repositories.user_repo import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, user_data: UserRegister) -> User:
        """
        Checks for duplicates, hashes password, and persists the new user.
        """
        # 1. Check for duplicates using the Repo
        # Note: Your UserRepo needs to support the 'or_' query logic shown in your original route.
        # Assuming your updated UserRepo has 'get_by_username_or_email' as shown in your upload.
        if self.user_repo.get_by_username_or_email(user_data.username, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or Email already registered"
            )

        # 2. Hash Password
        hashed_pw = get_password_hash(user_data.password)

        # 3. Create User Instance
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw,
            credits=0
        )

        # 4. Persist to DB
        try:
            self.user_repo.create(new_user) # Assuming BaseRepository has a .create() or .add()
            # If your Repo doesn't auto-commit, you might need:
            # self.user_repo.db.add(new_user)
            # self.user_repo.db.commit()
            # self.user_repo.db.refresh(new_user)
            return new_user
        except SQLAlchemyError:
            self.user_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during registration"
            )

    def authenticate_user(self, username: str, password: str) -> dict:
        """
        Verifies credentials and returns an access token.
        """
        user = self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password"
            )

        # Generate Token
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}