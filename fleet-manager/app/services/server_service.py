# backend/app/services/server_service.py
import uuid
import secrets
import os
import httpx
from fastapi import HTTPException, status
from redis import Redis
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.manager import ServerManager
    
from app.repositories.server_repo import ServerRepository
from app.schemas.schemas import ValheimConfigValidator

class ServerService:
    def __init__(
        self, 
        server_repo: ServerRepository,
        manager: "ServerManager", 
        redis: Redis
    ):
        self.server_repo = server_repo
        self.manager = manager
        self.redis = redis
        # Fetch the internal Identity Service URL from the environment
        self.identity_api_url = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:8000/api")

    async def _get_user_credits(self, user_id: str) -> float:
        """Helper method to fetch user credits from the Identity Service asynchronously."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.identity_api_url}/users/{user_id}/credits")
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail="User not found in Identity Service.")
                response.raise_for_status()
                data = response.json()
                return data.get("credits", 0.0)
            except httpx.RequestError as e:
                # Log the exception (e) in a real environment
                raise HTTPException(status_code=503, detail="Identity service is currently unavailable.")

    def list_servers(self):
        """Wraps the manager's list function."""
        return self.manager.list_all_servers()

    def get_server_details(self, server_id: str):
        """Combines Docker container info with Redis stats."""
        container = self.manager.get_container(server_id)
        if not container:
            raise HTTPException(status_code=404, detail="Server container not found")

        stats_key = f"server_stats:{server_id}"
        stats = self.redis.hgetall(stats_key)

        # Handle potential byte returns from Redis depending on the client config
        cpu = float(stats.get(b"cpu", stats.get("cpu", 0)))
        ram = float(stats.get(b"ram", stats.get("ram", 0)))
        players = int(stats.get(b"players", stats.get("players", 0)))

        return {
            "id": server_id,
            "name": container.name,
            "status": "online" if container.status == "running" else "offline",
            "cpu": cpu,
            "ram": ram,
            "players": players
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
            # 1. Async Credit Check via internal microservice API
            credits = await self._get_user_credits(user_id)
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
        
        # 1. Async Credit Check via internal microservice API
        credits = await self._get_user_credits(user_id)
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