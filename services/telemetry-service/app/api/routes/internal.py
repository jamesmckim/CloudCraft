# /telemetry-service/app/api/routes/internal.py
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.schemas.schemas import LogPayload, SidecarMetrics
from app.services.telemetry_service import TelemetryService
from app.api.dependencies import get_telemetry_service
from app.core.auth import verify_sidecar_token

router = APIRouter(tags=["Internal Sidecar"])

@router.post("/{server_id}/logs", dependencies=[Depends(verify_sidecar_token)])
async def receive_sidecar_logs(
    server_id: str, 
    payload: LogPayload,
    service: TelemetryService = Depends(get_telemetry_service)
):
    # Receives buffered logs from the game server sidecar.
    return service.process_logs(server_id, payload.logs)

@router.post("/{server_id}/metrics", dependencies=[Depends(verify_sidecar_token)])
async def receive_sidecar_metrics(
    server_id: str, 
    metrics: SidecarMetrics,
    service: TelemetryService = Depends(get_telemetry_service)
):
    # Receives live player counts and performance metrics.
    return service.process_metrics(server_id, metrics)