# /backend/app/api/routes/internal.py
import os
import secrets
from fastapi import APIRouter, Depends, Header, HTTPException, status
from redis import Redis


from app.schemas.schemas import LogPayload, SidecarMetrics
from app.services.telemetry_service import TelemetryService
from app.dependencies import get_telemetry_service, get_server_manager, get_redis
from app.core.manager import ServerManager

router = APIRouter(tags=["Internal Sidecar"])

# The secret key shared between the Manager API and the Sidecars
INTERNAL_SECRET = os.getenv("SIDECAR_API_KEY", "super-secret-internal-key-change-me")

def verify_dynamic_token(
    server_id: str,
    x_sidecar_token: str = Header(None),
    redis: Redis = Depends(get_redis)
):
    expected_token = redis.get(f"sidecar_auth:{server_id}")
    
    if not x_sidecar_token or x_sidecar_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized sidecar")

def verify_internal_token(x_sidecar_token: str = Header(None)):
    """Validates that the request is actually coming from our sidecar."""
    if not x_sidecar_token or x_sidecar_token != INTERNAL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing sidecar token"
        )

@router.post("/{server_id}/logs", dependencies=[Depends(verify_internal_token)])
async def receive_sidecar_logs(
    server_id: str, 
    payload: LogPayload,
    service: TelemetryService = Depends(get_telemetry_service)
):
    """Receives buffered logs from the game server sidecar."""
    return service.process_logs(server_id, payload.logs)

@router.post("/{server_id}/metrics", dependencies=[Depends(verify_internal_token)])
async def receive_sidecar_metrics(
    server_id: str, 
    metrics: SidecarMetrics,
    service: TelemetryService = Depends(get_telemetry_service)
):
    """Receives live player counts and performance metrics."""
    return service.process_metrics(server_id, metrics)

@router.post("/{server_id}/stop", dependencies=[Depends(verify_internal_token)])
async def handle_idle_shutdown(
    server_id: str,
    manager: ServerManager = Depends(get_server_manager)
):
    """Allows the sidecar to self-report an idle timeout and request destruction."""
    # Since the sidecar has proven its identity via the token, 
    # we can trust it to command its own shutdown.
    manager.stop_server(server_id)
    return {"status": "shutdown_initiated", "server_id": server_id}