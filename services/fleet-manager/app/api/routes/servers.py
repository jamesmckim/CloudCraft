# /fleet-manager/app/api/routes/servers.py
from fastapi import APIRouter, Depends
from typing import List

from app.core.security import get_current_user_id
from app.dependencies import get_server_service 
from app.services.server_service import ServerService
from app.schemas.schemas import GameDeploymentPayload, PowerActionPayload

router = APIRouter(tags=["Servers"])

@router.get("")
async def list_servers(
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Lists all available servers. 
    Requires valid auth (user_id)
    """
    return service.list_servers(user_id)

@router.get("/{server_id}")
async def get_server_details(
    server_id: str, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Gets details for a specific server, including live Redis stats.
    """
    return service.get_server_details(server_id)

@router.post("/{server_id}/power")
async def power_action(
    server_id: str, 
    payload: PowerActionPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Handles Start/Stop actions with async credit checks.
    """
    return await service.toggle_power(user_id, server_id, payload.action)

@router.post("/deploy")
async def deploy_new_server(
    payload: GameDeploymentPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Deploys a new game server container.
    """
    return await service.deploy_server(user_id, payload.game_id, payload.config)