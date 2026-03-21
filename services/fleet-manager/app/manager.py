# /fleet-manager/manager.py
import os
import copy
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.core.config import settings
# --- 1. LOAD CONFIGURATIONS ---

# --- 2. THE MANAGER (The "Kubernetes-Native" Brain) ---
class ServerManager:
    def __init__(self, game_templates, game_settings):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config() # Fallback for local testing
        
        self.GAME_TEMPLATES = game_templates
        self.SETTINGS = game_settings
        self.core_v1 = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        
        self.namespace = settings.NAMESPACE
        
        agones_settings = self.SETTINGS.get('agones', {})

        self.group = agones_settings.get('group', 'agones.dev')
        self.version = agones_settings.get('version', 'v1')
        self.plural = agones_settings.get('plural', 'gameservers')

    def _ensure_pvc_exists(self, logical_server_id: str):
        """Ensures the user has a permanent hard drive for this specific game."""
        pvc_name = f"world-pvc-{logical_server_id}"
        
        try:
            self.core_v1.read_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=self.namespace
            )
        except ApiException as e:
            if e.status == 404:
                print(f"Provisioning new storage volume: {pvc_name}")
                pvc_manifest = client.V1PersistentVolumeClaim(
                    metadata=client.V1ObjectMeta(name=pvc_name),
                    spec=client.V1PersistentVolumeClaimSpec(
                        access_modes=["ReadWriteOnce"],
                        resources=client.V1ResourceRequirements(requests={"storage": "10Gi"})
                    )
                )
                self.core_v1.create_namespaced_persistent_volume_claim(
                    namespace=self.namespace, body=pvc_manifest
                )
            else:
                raise e
        return pvc_name

    def _build_manifest(self, game_id: str, user_id: str, config_data: dict, logical_server_id: str, sidecar_token: str):
        """Constructs the Agones GameServer YAML using the Template Registry."""
        # Determine mod state from config (default to vanilla)
        is_modded = config_data.get("is_modded", False)
        mod_state = "modded" if is_modded else "vanilla"
        
        # Fetch the blueprint
        blueprint = self.GAME_TEMPLATES.get(game_id, {}).get(mod_state)
        if not blueprint:
            raise ValueError(f"No template found for {game_id} ({mod_state})")

        # Provision/Fetch the player's storage drive
        pvc_name = self._ensure_pvc_exists(logical_server_id)
        
        # Merge user config with blueprint defaults
        final_env = copy.deepcopy(blueprint.get("env_defaults", []))
        for k, v in config_data.items():
            if k != "is_modded": # Don't pass our internal flag to the game
                final_env.append({"name": k, "value": str(v)})
        
        app_settings = self.SETTINGS.get('app', {})
        manager_api_url = settings.MANAGER_API_URL
        telemetry_api_url = settings.TELEMETRY_API_URL
        
        # 1. Grab the initContainers from the blueprint (if they exist)
        init_containers = copy.deepcopy(blueprint.get("initContainers", []))
        
        # 2. Inject the Mod URLs into the initContainer's environment
        mod_urls_string = config_data.get("mod_urls", "") # Your API passes this in
        
        for ic in init_containers:
            if ic["name"] == "mod-downloader":
                for env_var in ic.get("env", []):
                    if env_var["name"] == "MOD_URLS":
                        env_var["value"] = mod_urls_string

        # 3. Add initContainers to the pod spec
        # I have a side car image setup, just need to change the Avtivity-sidecar
        # replace image -- remove CMD -- remove volume sidecar-scripts-volume
        manifest_spec_template_spec = {
            "containers": [
                {
                    "name": "game-engine",
                    "image": blueprint["image"],
                    "env": final_env,
                    "volumeMounts": [{"name": "world-data", "mountPath": "/config"}]
                },
                {
                    "name": "activity-sidecar",
                    "image": "python:3.14.1-alpine3.23",
                    "command": ["python", "-u", "/app/main.py"],
                    "env": [
                        {"name": "GAME_TYPE", "value": game_id},
                        {"name": "MANAGER_API_URL", "value": manager_api_url},
                        {"name": "TELEMETRY_API_URL", "value": telemetry_api_url},
                        {"name": "SIDECAR_API_KEY", "value": sidecar_token},
                        {"name": "SERVER_UUID", "value": str(logical_server_id)},
                        {
                            "name": "TARGET_CONTAINER_NAME",
                            "valueFrom": {
                                "fieldRef": {
                                    "fieldPath": "metadata.name"
                                }
                            }
                        }
                    ],
                    "volumeMounts": [
                        {"name": "world-data", "mountPath": "/config", "readOnly": True},
                        {"name": "sidecar-scripts-volume", "mountPath": "/app"}
                    ]
                }
            ],
            "volumes": [
                {"name": "world-data", "persistentVolumeClaim": {"claimName": pvc_name}},
                {"name": "sidecar-scripts-volume", "configMap": {"name": "sidecar-scripts"}}
            ]
        }
        
        # Only add the initContainers key if there are actually containers to run
        if init_containers:
            manifest_spec_template_spec["initContainers"] = init_containers
        
        return {
            "apiVersion": f"{self.group}/{self.version}",
            "kind": "GameServer",
            "metadata": {
                "generateName": f"{game_id}-{mod_state}-{user_id}-",
                "labels": {
                    "craftcloud.role": "game_sidecar",
                    "craftcloud.server_id": str(logical_server_id),
                    "game": game_id,
                    "mod_state": mod_state,
                    "owner_id": str(user_id),
                    "role": "game-sidecar"
                }
            },
            "spec": {
                "container": "game-engine",
                "ports": blueprint.get("ports", []),
                "template": {
                    "spec": manifest_spec_template_spec
                }
            }
        }

    def create_server(self, game_id: str, user_id: str, logical_server_id: str, sidecar_token: str, config_data: dict = None):
        if config_data is None:
            config_data = {}
            
        manifest = self._build_manifest(game_id, user_id, config_data, logical_server_id, sidecar_token)
        
        try:
            response = self.custom_api.create_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                body=manifest
            )
            
            # Return an object that mimics your expected container schema
            class MockContainer:
                def __init__(self, name):
                    self.name = name
                    self.status = "starting"
            
            return MockContainer(name=response["metadata"]["name"])
        except ApiException as e:
            print(f"Kubernetes Deployment Error: {e}")
            raise Exception("Failed to execute Kubernetes deployment.")

    def get_container(self, server_id: str):
        try:
            gs = self.custom_api.get_namespaced_custom_object(
                group=self.group, version=self.version, namespace=self.namespace,
                plural=self.plural, name=server_id
            )
            state = gs.get("status", {}).get("state", "Unknown")
            is_running = state in ["Ready", "Allocated"]
            
            class MockContainer:
                def __init__(self, name, status):
                    self.name = name
                    self.status = "running" if status else "offline"
            return MockContainer(name=server_id, status=is_running)
        except ApiException:
            return None

    def stop_server(self, server_id: str):
        try:
            self.custom_api.delete_namespaced_custom_object(
                group=self.group, version=self.version, namespace=self.namespace,
                plural=self.plural, name=server_id
            )
        except ApiException as e:
            if e.status != 404:
                print(f"Error stopping server: {e}")
    
    def delete_server_and_data(self, server_id: str, logical_server_id: str):
        """Stops the game server and permanently deletes the world data (PVC)."""
        """ Not Yet implemented """
        self.stop_server(server_id)
        
        pvc_name = f"world-pvc-{logical_server_id}"
        try:
            print(f"Permanently deleting storage volume: {pvc_name}")
            self.core_v1.delete_namespaced_persistent_volume_claim(
                name=pvc_name, 
                namespace=self.namespace
            )
        except ApiException as e:
            if e.status == 404:
                print(f"Volume {pvc_name} already deleted or not found.")
            else:
                print(f"Error deleting PVC {pvc_name}: {e}")
                raise e

    def list_all_servers(self):
        server_list = []
        try:
            gameservers = self.custom_api.list_namespaced_custom_object(
                group=self.group, version=self.version, namespace=self.namespace,
                plural=self.plural
            )
            for gs in gameservers.get("items", []):
                metadata = gs.get("metadata", {})
                status = gs.get("status", {})
                current_state = status.get("state", "Unknown")
                
                server_list.append({
                    "id": metadata.get("name"),
                    "name": metadata.get("name").replace("-", " ").title(),
                    "status": "online" if current_state in ["Ready", "Allocated"] else "offline",
                    "cpu": 0, "ram": 0, "players": 0 
                })
        except ApiException as e:
            print(f"Failed to list servers: {e}")
        return server_list