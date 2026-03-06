# /backend/app/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from redis import Redis
from functools import lru_cache

from app.manager import ServerManager

from app.core.database import get_db
from app.repositories.server_repo import ServerRepository
from app.services.server_service import ServerService


# Placeholder: Initialize these according to your specific environment configuration
def get_redis() -> Redis:
    return Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_server_manager() -> ServerManager:
    return ServerManager(game_templates={}, game_settings={})

def get_server_repo(db: Session = Depends(get_db)) -> ServerRepository:
    return ServerRepository(db)

def get_server_service(
    server_repo: ServerRepository = Depends(get_server_repo),
    manager: ServerManager = Depends(get_server_manager),
    redis: Redis = Depends(get_redis)
) -> ServerService:
    return ServerService(server_repo=server_repo, manager=manager, redis=redis)