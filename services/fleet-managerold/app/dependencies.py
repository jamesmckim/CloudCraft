# /fleet-manager/app/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from redis import Redis

from app.manager import ServerManager
from app.core.database import get_db, settings
from app.repositories.server_repo import ServerRepository
from app.services.server_service import ServerService
from app.clients.identity_client import IdentityServiceClient
from app.config.reader import GAME_TEMPLATES, SETTINGS

_redis_client: Redis | None = None
_server_manager: ServerManager | None = None
_identity_client: IdentityServiceClient | None = None

def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        # Utilizing the computed property from config.py
        _redis_client = Redis.from_url(
            settings.redis_url, 
            decode_responses=True
        )
    return _redis_client

def get_server_manager() -> ServerManager:
    global _server_manager
    if _server_manager is None:
        _server_manager = ServerManager(
            game_templates=GAME_TEMPLATES,
            game_settings={}
        )
    return _server_manager

def get_server_repo(db: Session = Depends(get_db)) -> ServerRepository:
    return ServerRepository(db)

def get_identity_client() -> IdentityServiceClient:
    global _identity_client
    if _identity_client is None:
        _identity_client = IdentityServiceClient()
    return _identity_client

def get_server_service(
    server_repo: ServerRepository = Depends(get_server_repo),
    manager: ServerManager = Depends(get_server_manager),
    redis: Redis = Depends(get_redis),
    identity_client: IdentityServiceClient = Depends(get_identity_client)
) -> ServerService:
    return ServerService(
        server_repo=server_repo, 
        manager=manager, 
        redis=redis,
        identity_client=identity_client
    )