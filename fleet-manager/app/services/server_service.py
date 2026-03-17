# /fleet-manager/app/services/server_service.py
import uuid
import secrets
import os
from fastapi import HTTPException, status
from redis import Redis
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.manager import ServerManager
    
from app.repositories.server_repo import ServerRepository
from app.schemas.schemas import ValheimConfigValidator
from app.clients.identity_client import IdentityServiceClient

class ServerService:
    def __init__(
        self, 
        server_repo: ServerRepository,
        manager: "ServerManager", 
        redis: Redis,
        identity_client: IdentityServiceClient
    ):
        self.server_repo = server_repo
        self.manager = manager
        self.redis = redis
        self.identity_client = identity_client

    def list_servers(self, user_id: str):
        """Fetches servers from the database so the UUID is preserved and filtered by owner."""
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format.")
            
        db_servers = self.server_repo.get_by_owner(user_id_int) 
        
        server_list = []
        for server_record in db_servers:
            is_online = False
            if server_record.active_pod_name:
                container = self.manager.get_container(server_record.active_pod_name)
                is_online = container is not None and container.status == "running"
            
            custom_name = None
            if server_record.config:
                custom_name = server_record.config.get("VALHEIM_SERVER_NAME")
                
            display_name = custom_name if custom_name else f"{server_record.game_id} Server".title()
            
            server_list.append({
                "id": server_record.id,
                "name": display_name,
                "status": "online" if is_online else "offline",
                "cpu": 0, 
                "ram": 0, 
                "players": 0 
            })
            
        return server_list

    def get_server_details(self, server_id: str):
        """Combines K8s container info with Redis stats using the DB as the source of truth."""
        server_record = self.server_repo.get(server_id)
        if not server_record:
            raise HTTPException(status_code=404, detail="Server not found in database")

        container = None
        if server_record.active_pod_name:
            container = self.manager.get_container(server_record.active_pod_name)

        stats_key = f"server_stats:{server_id}"
        stats = self.redis.hgetall(stats_key)

        cpu = float(stats.get(b"cpu", stats.get("cpu", 0)))
        ram = float(stats.get(b"ram", stats.get("ram", 0)))
        players = int(stats.get(b"players", stats.get("players", 0)))

        is_online = container is not None and getattr(container, "status", "") == "running"

        custom_name = None
        if server_record.config:
            custom_name = server_record.config.get("VALHEIM_SERVER_NAME")
            
        display_name = custom_name if custom_name else f"{server_record.game_id} Server".title()

        return {
            "id": server_record.id,
            "name": display_name,
            "status": "online" if is_online else "offline",
            "cpu": cpu if is_online else 0,
            "ram": ram if is_online else 0,
            "players": players if is_online else 0
        }

    async def toggle_power(self, user_id: str, server_id: str, action: str):
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format.")
            
        server_record = self.server_repo.get(server_id)
        
        if not server_record:
            raise HTTPException(status_code=404, detail="Server not registered in database.")
            
        if str(server_record.owner_id) != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this server.")

        if action == "stop":
            if not server_record.active_pod_name or not self.manager.get_container(server_record.active_pod_name):
                raise HTTPException(status_code=404, detail="Server instance not found or already stopped.")
                
            self.manager.stop_server(server_record.active_pod_name)
            self.server_repo.update(server_record, {"active_pod_name": None})

        elif action == "start":
            # 1. Async Credit Check via injected client
            credits = await self.identity_client.get_user_credits(user_id)
            if credits <= 1.0:
                raise HTTPException(status_code=402, detail="Insufficient credits.")
            
            if server_record.active_pod_name and self.manager.get_container(server_record.active_pod_name):
                return {"status": "already_running"}
            
            ephemeral_sidecar_token = secrets.token_hex(16)
            self.redis.set(f"sidecar_auth:{server_id}", ephemeral_sidecar_token)
            
            new_container = self.manager.create_server(
                game_id=server_record.game_id,
                user_id=user_id,
                logical_server_id=server_id,
                sidecar_token=ephemeral_sidecar_token,
                config_data=server_record.config
            )
            
            self.server_repo.update(server_record, {"active_pod_name": new_container.name})
        
        return {"result": "success", "status": "processing"}

    async def deploy_server(self, user_id: str, game_id: str, config: dict):
        if game_id == "valheim":
            try:
                config = ValheimConfigValidator(**config).dict()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
        # 1. Async Credit Check via injected client
        credits = await self.identity_client.get_user_credits(user_id)
        if credits < 5.0:
            raise HTTPException(status_code=402, detail="Insufficient credits.")
        
        logical_server_id = str(uuid.uuid4())
        ephemeral_sidecar_token = secrets.token_hex(16)
        
        self.redis.set(f"sidecar_auth:{logical_server_id}", ephemeral_sidecar_token)
        
        new_container = self.manager.create_server(
            game_id=game_id,
            user_id=user_id,
            logical_server_id=logical_server_id,
            sidecar_token=ephemeral_sidecar_token,
            config_data=config
        )
        
        try:
            self.server_repo.create({
                "id": logical_server_id,
                "owner_id": user_id_int,
                "game_id": game_id,
                "config": config,
                "active_pod_name": new_container.name,
                "hourly_cost": 0.10
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to register server: {str(e)}")

        return {"status": "success", "server_id": logical_server_id}