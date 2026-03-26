# /telemetry-service/app/api/routes/incidents.py
from fastapi import APIRouter, Depends

from app.services.incident_service import IncidentService
from app.api.dependencies import get_incident_service
from app.core.auth import get_current_user_stateless

router = APIRouter(tags=["Incidents"])

@router.get("/{server_id}")
async def get_server_incidents(
    server_id: str, 
    service: IncidentService = Depends(get_incident_service),
    user_id: str = Depends(get_current_user_stateless) # Validates JWT Statelessly
):
    return await service.get_server_incidents(server_id)

@router.get("/{server_id}/resolve/{task_id}")
async def resolve_ai_incident(
    server_id: str, 
    task_id: str, 
    service: IncidentService = Depends(get_incident_service),
    user_id: str = Depends(get_current_user_stateless) # Validates JWT Statelessly
):
    return await service.resolve_ai_incident(server_id, task_id)