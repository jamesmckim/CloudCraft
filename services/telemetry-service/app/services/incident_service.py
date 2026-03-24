# /telemetry-service/app/services/incident_service.py
from fastapi import HTTPException
from arq.jobs import Job, JobStatus
from arq.connections import ArqRedis

from app.models.models import IncidentReport
from app.repositories.incident_repo import IncidentRepository

class IncidentService:
    def __init__(self, incident_repo: IncidentRepository, arq_pool: ArqRedis):
        self.repo = incident_repo
        self.arq_pool = arq_pool

    def get_server_incidents(self, server_id: str, limit: int = 10):
        # Retrieves the most recent incidents for a specific server.
        return self.repo.get_recent_by_server(server_id, limit)

    def resolve_ai_incident(self, server_id: str, task_id: str):
        # Checks the status of an AI analysis task. If successful, persists the result as a new IncidentReport.
        
        result = AsyncResult(task_id, app=self.celery)
        
        if not result.ready():
            return {"status": "pending"}
            
        data = result.result
        
        if not data or data.get("status") == "error":
            result.forget()
            return {
                "status": "error", 
                "detail": data.get("error_message", "Unknown error") if data else "No data returned"
            }
            
        new_incident = IncidentReport(
            server_id=server_id,
            error_line=data.get("error_line"),
            recommendation=data.get("recommendation")
        )
        
        try:
            self.repo.db.add(new_incident)
            self.repo.db.commit()
            self.repo.db.refresh(new_incident)
        except Exception as e:
            self.repo.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save incident to database.")
        
        result.forget() 
        
        return {
            "status": "completed",
            "incident": new_incident
        }