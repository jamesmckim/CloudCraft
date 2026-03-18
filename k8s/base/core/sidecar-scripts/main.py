import os
import time
import json
import urllib.request
import urllib.error
from probes import get_probe

# Config from Env
SERVER_UUID = os.getenv('SERVER_UUID')
GAME_TYPE = os.getenv('GAME_TYPE', 'generic')
API_URL = os.getenv('MANAGER_API_URL')
THRESHOLD = int(os.getenv('IDLE_THRESHOLD_MINUTES', 15)) * 60 
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/config/server.log')
SIDECAR_API_KEY = os.getenv('SIDECAR_API_KEY')

AGONES_SDK_URL = "http://localhost:9358"

probe = get_probe(GAME_TYPE)
idle_seconds = 0
# FIX 1: Must be less than the 5-second Agones health period
sleep_secs = 2 
is_ready = False

def send_manager_request(endpoint, payload=None):
    url = f"{API_URL}/internal/servers/{SERVER_UUID}/{endpoint}"
    try:
        req = urllib.request.Request(url, method='POST')
        req.add_header('X-Sidecar-Token', SIDECAR_API_KEY)
        if payload:
            data = json.dumps(payload).encode('utf-8')
            req.data = data
            req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Failed to contact manager at {endpoint}: {e}")

def send_agones_request(endpoint):
    url = f"{AGONES_SDK_URL}/{endpoint}"
    try:
        req = urllib.request.Request(url, data=b'{}', method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        pass # Suppress prints here to avoid log spam every 2 seconds

try:
    log_file = open(LOG_FILE_PATH, 'r')
    log_file.seek(0, os.SEEK_END)
except FileNotFoundError:
    log_file = None

while True:
    try:
        # FIX 2: ALWAYS send the health ping first, no matter what!
        # This prevents Agones from killing the pod while Valheim downloads.
        send_agones_request("health")
        
        # 1. Check Player Activity & Readiness
        try:
            players = probe.get_player_count()
            
            if players >= 0 and not is_ready:
                print("Server is responding on game port. Telling Agones we are Ready!")
                send_agones_request("ready")
                is_ready = True
                
        except Exception:
            players = -1
            # Game is still downloading or booting, which is perfectly fine.
        
        # 2. Handle Scaling Down
        if players == 0 and is_ready: # Only count idle time if fully booted
            idle_seconds += sleep_secs
        else:
            idle_seconds = 0
            
        if idle_seconds >= THRESHOLD:
            print(f"Idle threshold met. Requesting shutdown...")
            send_manager_request("stop")
            send_agones_request("shutdown")
            break

        # 3. Report stats
        if is_ready:
            send_manager_request("metrics", {"players": players})
        
        # 4. Tail Logs
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
        print(f"Error in sidecar main loop: {e}")

    time.sleep(sleep_secs)