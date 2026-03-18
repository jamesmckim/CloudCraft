# backend/app/repositories/server_repo.py
from sqlalchemy.orm import Session

from app.models.models import Server
from app.repositories.base import BaseRepository

class ServerRepository(BaseRepository[Server]):
    def __init__(self, db: Session):
        super().__init__(db, Server)

    def get_by_owner(self, owner_id: int):
        """Retrieve all servers owned by a specific user."""
        return self.db.query(Server).filter(Server.owner_id == owner_id).all()