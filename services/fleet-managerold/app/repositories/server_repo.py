# /fleet-manager/app/repositories/server_repo.py
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.models.models import Server
from app.repositories.base import BaseRepository

class ServerRepository(BaseRepository[Server]):
    def __init__(self, db: Session):
        super().__init__(db, Server)

    async def get_by_owner(self, owner_id: int):
        """Retrieve all servers owned by a specific user."""
        stmt = select(Server).where(Server.owner_id == owner_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()