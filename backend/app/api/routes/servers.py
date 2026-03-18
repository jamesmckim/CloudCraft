# /backend/app/api/routes/servers.py
from fastapi import APIRouter, Depends
from typing import List

from app.core.security import get_current_user_id
from app.dependencies import get_server_service 
from app.services.server_service import ServerService
from app.schemas.schemas import GameDeploymentPayload, PowerActionPayload

router = APIRouter(tags=["Servers"])

@router.get("/")
def list_servers(
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Lists all available servers. 
    Requires valid auth (user_id), but lists global servers for now.
    """
    return service.list_servers()

@router.get("/{server_id}")
def get_server_details(
    server_id: str, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Gets details for a specific server, including live Redis stats.
    """
    return service.get_server_details(server_id)

@router.post("/{server_id}/power")
def power_action(
    server_id: str, 
    payload: PowerActionPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Handles Start/Stop actions with credit checks.
    """
    # Note: Access Pydantic model fields directly (.action), not via .get()
    return service.toggle_power(user_id, server_id, payload.action)

@router.post("/deploy")
def deploy_new_server(
    payload: GameDeploymentPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Deploys a new game server container.
    """
    return service.deploy_server(user_id, payload.game_id, payload.config)