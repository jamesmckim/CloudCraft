# /backend/app/api/routes/incidents.py
from fastapi import APIRouter, Depends

# custom
from app.services.incident_service import IncidentService
from app.dependencies import get_incident_service

router = APIRouter(tags=["Incidents"])

@router.get("/{server_id}/incidents")
def get_server_incidents(
    server_id: str, 
    service: IncidentService = Depends(get_incident_service)
):
    return service.get_server_incidents(server_id)

@router.get("/{server_id}/incidents/resolve/{task_id}")
def resolve_ai_incident(
    server_id: str, 
    task_id: str, 
    service: IncidentService = Depends(get_incident_service)
):
    return service.resolve_ai_incident(server_id, task_id)