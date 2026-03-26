# /telemetry-service/app/repositories/incident_repo.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import IncidentReport
from app.repositories.base import BaseRepository

class IncidentRepository(BaseRepository[IncidentReport]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, IncidentReport)

    async def get_recent_by_server(self, server_id: str, limit: int = 10) -> List[IncidentReport]:
        stmt = (
            select(IncidentReport)
            .where(IncidentReport.server_id == server_id)
            .order_by(IncidentReport.created_at.desc())
            .limit(limit)
        )
        result = await self.db.excute(stmt)
        return result.scalars().all()