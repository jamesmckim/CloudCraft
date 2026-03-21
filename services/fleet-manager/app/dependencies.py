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

def get_redis() -> Redis:
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )

def get_server_manager() -> ServerManager:
    return ServerManager(
        game_templates=GAME_TEMPLATES,
        game_settings={}
    )

def get_server_repo(db: Session = Depends(get_db)) -> ServerRepository:
    return ServerRepository(db)

def get_identity_client() -> IdentityServiceClient:
    return IdentityServiceClient()

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