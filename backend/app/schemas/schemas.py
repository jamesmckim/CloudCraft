# backend/schemas.py
from pydantic import BaseModel, Field, model_validator, EmailStr, ConfigDict
from typing import Optional, List, Literal

class GameDeploymentPayload(BaseModel):
    game_id: str
    config: dict
    
class ValheimConfigValidator(BaseModel):
    is_modded: bool = False
    mod_urls: Optional[str] = ""
    # Only allow alphanumeric characters, underscores, and hyphens, Max 30 chars.
    VALHEIM_SERVER_NAME: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_\-]+$")
    VALHEIM_WORLD_NAME: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_\-]+$")
    
    # Password must be at least 5 chars
    # Added pattern to allow alphanumeric and some safe symbols, rejecting spaces or shell operators
    VALHEIM_SERVER_PASS: str = Field(..., min_length=5, max_length=30, pattern=r"^[a-zA-Z0-9_\-\@\#\!\?\*]+$")
    
    # Restrict to safe cron characters: numbers, spaces, *, /, -, and ,
    # Max length of 60 prevents buffer overflow attempts
    VALHEIM_UPDATE_CRON: str = Field(
        default="0 6 * * *", 
        max_length=60,
        pattern=r"^[0-9\s\*\/\-\,]+$"
    )
    VALHEIM_BACKUPS_MAX_COUNT: int = Field(default=5, ge=1, le=20)

    @model_validator(mode='after')
    def check_valheim_password_rules(self) -> 'ValheimConfigValidator':
        # Valheim will reject the server start if the password contains the server or world name
        if self.VALHEIM_SERVER_NAME.lower() in self.VALHEIM_SERVER_PASS.lower():
            raise ValueError("Server password cannot contain the server name.")
        
        if self.VALHEIM_WORLD_NAME.lower() in self.VALHEIM_SERVER_PASS.lower():
            raise ValueError("Server password cannot contain the world name.")
            
        return self
    
class PowerActionPayload(BaseModel):
    action: Literal["start", "stop"]

# Metrics reported by sibling containers
class SidecarMetrics(BaseModel):
    cpu: float
    ram: float
    players: int

# Example: Future schema for deployment requests
class ServerDeploy(BaseModel):
    game_id: str
    region: Optional[str] = "us-east"

# Example: Data sent back to the user
class UserProfile(BaseModel):
    username: str
    email: EmailStr
    credits: float
    # Add this line to allow reading from SQLAlchemy models! (Pydantic v2)
    model_config = ConfigDict(from_attributes=True)

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class LogPayload(BaseModel):
    logs: List[str]