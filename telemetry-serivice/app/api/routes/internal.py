# /app/api/routes/internal.py
import os
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.schemas.schemas import LogPayload, SidecarMetrics
from app.services.telemetry_service import TelemetryService
from app.api.dependencies import get_telemetry_service

router = APIRouter(tags=["Internal Sidecar"])

# The secret key shared between the Manager API and the Sidecars.
INTERNAL_SECRET = os.getenv("SIDECAR_API_KEY", "super-secret-internal-key-change-me")

def verify_internal_token(x_sidecar_token: str = Header(None)):
    # Validates that the request is actually coming from our sidecar.
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
    # Receives buffered logs from the game server sidecar.
    return service.process_logs(server_id, payload.logs)

@router.post("/{server_id}/metrics", dependencies=[Depends(verify_internal_token)])
async def receive_sidecar_metrics(
    server_id: str, 
    metrics: SidecarMetrics,
    service: TelemetryService = Depends(get_telemetry_service)
):
    # Receives live player counts and performance metrics.
    return service.process_metrics(server_id, metrics)