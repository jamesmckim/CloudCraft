# /fleet-manager/app/schemas/schemas.py
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List, Literal

class GameDeploymentPayload(BaseModel):
    game_id: str
    config: dict
    
class ValheimConfigValidator(BaseModel):
    is_modded: bool = False
    mod_urls: Optional[str] = ""
    VALHEIM_SERVER_NAME: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_\-]+$")
    VALHEIM_WORLD_NAME: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_\-]+$")
    VALHEIM_SERVER_PASS: str = Field(..., min_length=5, max_length=30, pattern=r"^[a-zA-Z0-9_\-\@\#\!\?\*]+$")
    VALHEIM_UPDATE_CRON: str = Field(default="0 6 * * *", max_length=60, pattern=r"^[0-9\s\*\/\-\,]+$")
    VALHEIM_BACKUPS_MAX_COUNT: int = Field(default=5, ge=1, le=20)

    @model_validator(mode='after')
    def check_valheim_password_rules(self) -> 'ValheimConfigValidator':
        if self.VALHEIM_SERVER_NAME.lower() in self.VALHEIM_SERVER_PASS.lower():
            raise ValueError("Server password cannot contain the server name.")
        
        if self.VALHEIM_WORLD_NAME.lower() in self.VALHEIM_SERVER_PASS.lower():
            raise ValueError("Server password cannot contain the world name.")
            
        return self
    
class PowerActionPayload(BaseModel):
    action: Literal["start", "stop"]

class SidecarMetrics(BaseModel):
    cpu: float
    ram: float
    players: int

class ServerDeploy(BaseModel):
    game_id: str
    region: Optional[str] = "us-east"

class LogPayload(BaseModel):
    logs: List[str]