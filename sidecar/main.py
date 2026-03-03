import os
import time
import json
import urllib.request
import urllib.error
from probes import get_probe

# Config from Env
TARGET = os.getenv('TARGET_CONTAINER_NAME')
GAME_TYPE = os.getenv('GAME_TYPE', 'generic')
API_URL = os.getenv('MANAGER_API_URL')
THRESHOLD = int(os.getenv('IDLE_THRESHOLD_MINUTES', 15)) * 60 
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/config/server.log')

# --- NEW: Agones SDK Local Endpoint ---
AGONES_SDK_URL = "http://localhost:9340"

probe = get_probe(GAME_TYPE)
idle_seconds = 0
sleep_secs = 10
is_ready = False # Track if we've told Agones we are ready

def send_manager_request(endpoint, payload=None):
    """Sends custom metrics and logs back to your Manager API."""
    url = f"{API_URL}/servers/{TARGET}/{endpoint}"
    try:
        if payload:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method='POST')
            
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Failed to contact manager at {endpoint}: {e}")

def send_agones_request(endpoint):
    """Sends lifecycle commands to the local Agones SDK."""
    url = f"{AGONES_SDK_URL}/{endpoint}"
    try:
        req = urllib.request.Request(url, data=b'{}', method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Failed to contact Agones SDK at {endpoint}: {e}")

try:
    log_file = open(LOG_FILE_PATH, 'r')
    log_file.seek(0, os.SEEK_END)
except FileNotFoundError:
    log_file = None
    print(f"Warning: Log file {LOG_FILE_PATH} not found yet.")

while True:
    try:
        # 1. Check Player Activity (Proves the server is alive)
        try:
            players = probe.get_player_count()
            
            # --- NEW: Agones Ready & Health Pings ---
            if not is_ready:
                print("Server is responding. Telling Agones we are Ready!")
                send_agones_request("ready")
                is_ready = True
                
            # Send the heartbeat so Agones knows the server hasn't frozen
            send_agones_request("health")
            
        except Exception:
            players = 0
            # If the probe fails, we skip sending the Agones health ping.
            # If this happens too many times, Agones will mark the server Unhealthy.
        
        # 2. Handle Scaling Down
        if players == 0:
            idle_seconds += sleep_secs
        else:
            idle_seconds = 0
            
        if idle_seconds >= THRESHOLD:
            print(f"Idle threshold met. Requesting shutdown...")
            send_manager_request("stop") # Tell your API
            send_agones_request("shutdown") # Tell Agones to delete this Pod
            break

        # 3. Report stats to your Manager API
        send_manager_request("metrics", {"players": players})
        
        # 4. Tail Logs and send to Manager API
        if log_file:
            new_logs = []
            while True:
                line = log_file.readline()
                if not line:
                    break
                clean_line = line.strip()
                if clean_line:
                    new_logs.append(clean_line)
            if new_logs:
                send_manager_request("logs", {"logs": new_logs})
        else:
            try:
                log_file = open(LOG_FILE_PATH, 'r')
                log_file.seek(0, os.SEEK_END)
            except FileNotFoundError:
                pass

    except Exception as e:
        print(f"Error in sidecar: {e}")

    time.sleep(sleep_secs)