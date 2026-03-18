# backend/app/services/server_service.py
import uuid
import secrets
from fastapi import HTTPException, status
from redis import Redis

from app.dependencies import ServerManager
from app.repositories.user_repo import UserRepository
from app.repositories.server_repo import ServerRepository
from app.schemas.schemas import ValheimConfigValidator

class ServerService:
    def __init__(
        self, 
        user_repo: UserRepository, 
        server_repo: ServerRepository,
        manager: ServerManager, 
        redis: Redis
    ):
        self.user_repo = user_repo
        self.server_repo = server_repo
        self.manager = manager
        self.redis = redis

    def list_servers(self):
        """Wraps the manager's list function."""
        # Optional: You could now filter this by referencing self.server_repo if needed
        return self.manager.list_all_servers()

    def get_server_details(self, server_id: str):
        """Combines Docker container info with Redis stats."""
        # 1. Get static container info
        container = self.manager.get_container(server_id)
        if not container:
            raise HTTPException(status_code=404, detail="Server container not found")

        # 2. Fetch live stats from Redis
        stats_key = f"server_stats:{server_id}"
        stats = self.redis.hgetall(stats_key)

        # 3. Default to zero if no stats found
        cpu = float(stats.get("cpu", 0))
        ram = float(stats.get("ram", 0))
        players = int(stats.get("players", 0))

        return {
            "id": server_id,
            "name": container.name,
            "status": "online" if container.status == "running" else "offline",
            "cpu": cpu,
            "ram": ram,
            "players": players
        }

    def toggle_power(self, user_id: str, server_id: str, action: str):
        # Cast string to int need to condence this evantually, I'm doing this all over the place
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format.")
            
        # 1. [New] Ownership Check: Verify server exists in DB and belongs to user
        server_record = self.server_repo.get(server_id)
        
        if not server_record:
            raise HTTPException(status_code=404, detail="Server not registered in database.")
            
        # Ensure user_id is compared correctly
        if str(server_record.owner_id) != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this server.")

        # 3. Retrieve User for credit check
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User session invalid.")
        
        if action == "stop":
            # Logic Check: can't stop a server that doesn't exist
            if not server_record.active_pod_name or not self.manager.get_container(server_record.active_pod_name):
                raise HTTPException(status_code=404, detail="Server instance not found or already stopped.")
                
            self.manager.stop_server(server_record.active_pod_name)
            self.server_repo.update(server_record, {"active_pod_name": None})

        elif action == "start":
            # Business Logic: Check credits
            if user.credits <= 1.0:
                raise HTTPException(status_code=402, detail="Insufficient credits.")
            
            # Logic Check: Don't deploy a duplicate
            if server_record.active_pod_name and self.manager.get_container(server_record.active_pod_name):
                return {"status": "already_running"}
            
            # Generate the auth token for the new container
            ephemeral_sidecar_token = secrets.token_hex(16)
            self.redis.set(f"sidecar_auth:{server_id}", ephemeral_sidecar_token)
            
            new_container = self.manager.create_server(
                game_id=server_record.game_id,
                user_id=user_id,
                logical_server_id=server_id,
                sidecar_token=ephemeral_sidecar_token,
                config_data=server_record.config
            )
            
            # Update the DB with the new ephemeral pod name
            self.server_repo.update(server_record, {"active_pod_name": new_container.name})
        
        return {"result": "success", "status": "processing"}

    def deploy_server(self, user_id: str, game_id: str, config: dict):
        if game_id == "valheim":
            try:
                # Validate and sanitize using the Pydantic model
                config = ValheimConfigValidator(**config).dict()
            except Exception as e:
                print(f"Pydantic Validation Failed: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
        
        # Cast to integer safely
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
        # 1. Verify User and Credits
        user = self.user_repo.get(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        if user.credits < 5.0:
            raise HTTPException(status_code=402, detail="Insufficient credits.")
        
        logical_server_id = str(uuid.uuid4())
        
        ephemeral_sidecar_token = secrets.token_hex(16)
        
        self.redis.set(f"sidecar_auth:{logical_server_id}", ephemeral_sidecar_token)
        
        # 2. Create Docker Container
        new_container = self.manager.create_server(
            game_id=game_id,
            user_id=user_id,
            logical_server_id=logical_server_id,
            sidecar_token=ephemeral_sidecar_token,
            config_data=config
        )
        
        # 3. Save the master blueprint to the DB
        try:
            self.server_repo.create({
                "id": logical_server_id,
                "owner_id": user.id,
                "game_id": game_id,
                "config": config,
                "active_pod_name": new_container.name,
                "hourly_cost": 0.10 # Default cost
            })
        except Exception as e:
            # Rollback: If DB save fails, we should probably destroy the container 
            # to prevent 'orphan' servers, or log a critical error.
            # self.manager.delete_server(new_container.name) 
            raise HTTPException(status_code=500, detail=f"Failed to register server: {str(e)}")

        return {"status": "success", "server_id": logical_server_id}