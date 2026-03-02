# backend/manager.py
import os
import uuid
from dotenv import load_dotenv
from kubernetes import client, config
from kubernetes.client.rest import ApiException

load_dotenv()

# --- 1. THE MANAGER (The "Kubernetes-Native" Brain) ---
class ServerManager:
    def __init__(self):
        # SHIFT 1: The Connection
        # Instead of a local Docker socket, we use the internal Kubernetes cluster token
        try:
            config.load_incluster_config()
            self.custom_api = client.CustomObjectsApi()
            self.namespace = os.getenv("NAMESPACE", "craftcloud-system")
        except Exception as e:
            print(f"Kubernetes Connection Error: {e}")

    def list_all_servers(self):
        # SHIFT 2: The Listing
        # Instead of listing Docker containers, we list Agones "GameServers"
        server_list = []
        try:
            gameservers = self.custom_api.list_namespaced_custom_object(
                group="agones.dev",
                version="v1",
                namespace=self.namespace,
                plural="gameservers"
            )
            
            for gs in gameservers.get("items", []):
                metadata = gs.get("metadata", {})
                status = gs.get("status", {})
                
                # Agones tracks state in status.state (e.g., Ready, Allocated, Shutdown)
                current_state = status.get("state", "Unknown")
                
                server_list.append({
                    "id": metadata.get("name"),
                    "name": metadata.get("name").replace("-", " ").title(),
                    "status": "online" if current_state in ["Ready", "Allocated"] else "offline",
                    # Return default 0s to keep your frontend perfectly intact
                    "cpu": 0, 
                    "ram": 0,
                    "players": 0 
                })
        except ApiException as e:
            print(f"Failed to list servers: {e}")
            
        return server_list

    def get_container(self, server_id: str):
        # We keep the name 'get_container' so your existing API routes don't break
        try:
            return self.custom_api.get_namespaced_custom_object(
                group="agones.dev",
                version="v1",
                namespace=self.namespace,
                plural="gameservers",
                name=server_id
            )
        except ApiException:
            return None
    
    def stop_server(self, server_id):
        # SHIFT 3: The Teardown
        # Instead of stopping a container, we delete the GameServer resource
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="agones.dev",
                version="v1",
                namespace=self.namespace,
                plural="gameservers",
                name=server_id
            )
        except ApiException as e:
            print(f"Error stopping server: {e}")
    
    def start_logic(self, server_id: str):
        # Note: In Kubernetes, pods are generally ephemeral. 
        # If a server is 'stopped' (deleted), you typically use create_server to spin it up again.
        # If you meant 'unpause', Kubernetes doesn't pause pods natively like Docker does.
        pass

    def create_server(self, game_id: str, user_id: str, config_data: dict = None):
        if config_data is None:
            config_data = {}
            
        unique_suffix = str(uuid.uuid4())[:8]
        project_name = f"craftcloud-{game_id}-{unique_suffix}"
        
        # SHIFT 4: The Creation
        # Instead of subprocess and docker-compose, we build the exact Kubernetes 
        # manifest as a Python dictionary and post it directly to the API.
        
        # We combine both your Game and Sidecar into a single Pod blueprint
        manifest = {
            "apiVersion": "agones.dev/v1",
            "kind": "GameServer",
            "metadata": {
                "name": project_name,
                "labels": {
                    "craftcloud.role": "game_server",
                    "game": game_id,
                    "user": user_id
                }
            },
            "spec": {
                "ports": [{
                    "name": "default",
                    "portPolicy": "Dynamic",
                    "containerPort": 2456 # Valheim's default port
                }],
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": f"{game_id}-server",
                                # Update this to your actual game server image
                                "image": f"ghcr.io/your-username/{game_id}-server:latest", 
                                "env": [{"name": k, "value": str(v)} for k, v in config_data.items()]
                            },
                            {
                                "name": "sidecar-monitor",
                                # Update this to your actual sidecar image
                                "image": "valheim-sidecar-image", 
                                "env": [{"name": k, "value": str(v)} for k, v in config_data.items()]
                            }
                        ]
                    }
                }
            }
        }
        
        try:
            self.custom_api.create_namespaced_custom_object(
                group="agones.dev",
                version="v1",
                namespace=self.namespace,
                plural="gameservers",
                body=manifest
            )
            return self.get_container(project_name)
        except ApiException as e:
            print(f"Kubernetes Deployment Error: {e}")
            raise Exception("Failed to execute Kubernetes deployment.")