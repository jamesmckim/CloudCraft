# /backend/app/services/incident_service.py
from celery import Celery
from celery.result import AsyncResult
from fastapi import HTTPException

from app.models.models import IncidentReport
from app.repositories.incident_repo import IncidentRepository

class IncidentService:
    def __init__(self, incident_repo: IncidentRepository, celery_app: Celery):
        self.repo = incident_repo
        self.celery = celery_app

    def get_server_incidents(self, server_id: str, limit: int = 10):
        """
        Retrieves the most recent incidents for a specific server.
        """
        return self.repo.get_recent_by_server(server_id, limit)

    def resolve_ai_incident(self, server_id: str, task_id: str):
        """
        Checks the status of an AI analysis task. 
        If successful, persists the result as a new IncidentReport.
        """
        result = AsyncResult(task_id, app=self.celery)
        
        if not result.ready():
            return {"status": "pending"}
            
        data = result.result
        
        # Handle failures or empty results from the worker
        if not data or data.get("status") == "error":
            result.forget()
            return {
                "status": "error", 
                "detail": data.get("error_message", "Unknown error") if data else "No data returned"
            }
            
        # Create the new incident object
        new_incident = IncidentReport(
            server_id=server_id,
            error_line=data.get("error_line"),
            recommendation=data.get("recommendation")
        )
        
        # Persist using the repository
        # Assuming BaseRepository has a standard .create() or .add() method.
        # If not, we access the session directly via self.repo.db
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