# /identity-billing-service/app/repositories/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by their numeric database ID."""
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their unique username."""
        stmt = select(User).filter(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their unique email."""
        stmt = select(User).filter(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_username_or_email(self, username: str, email: str) -> User | None:
        """
        Checks if a user exists with either the given username OR email.
        """
        stmt = select(User).filter(
            or_(User.username == username, User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def add_credits(self, user_id: str, amount: int):
        try:
            db_id = int(user_id)
        except ValueError:
            return None 
            
        user = await self.get_by_id(db_id)
        if user:
            user.credits += amount
            await self.db.commit()
            await self.db.refresh(user)
            return user
        return None