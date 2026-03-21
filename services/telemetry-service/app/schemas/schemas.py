# /telemetry-service/app/schemas/schemas.py
from typing import List
from pydantic import BaseModel

class LogPayload(BaseModel):
    logs: List[str]

class SidecarMetrics(BaseModel):
    # Adjust these fields based on what your sidecar actually sends
    cpu_usage: float
    memory_usage: float
    active_players: int
    uptime_seconds: int