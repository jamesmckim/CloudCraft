# /telemetry-service/app/repositories/incident_repo.py
from typing import List
from sqlalchemy.orm import Session

from app.models.models import IncidentReport
from app.repositories.base import BaseRepository

class IncidentRepository(BaseRepository[IncidentReport]):
    def __init__(self, db: Session):
        super().__init__(db, IncidentReport)

    def get_recent_by_server(self, server_id: str, limit: int = 10) -> List[IncidentReport]:
        return (
            self.db.query(IncidentReport)
            .filter(IncidentReport.server_id == server_id)
            .order_by(IncidentReport.created_at.desc())
            .limit(limit)
            .all()
        )