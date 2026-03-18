# sidecar/probes.py
import socket

class BaseProbe:
    def get_player_count(self):
        return 0

class ValheimProbe(BaseProbe):
    def get_player_count(self):
        # Valheim uses A2S Query on port 2457
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            # Standard A2S_INFO challenge
            sock.sendto(b'\xff\xff\xff\xffTSource Engine Query\x00', ("127.0.0.1", 2457))
            data, _ = sock.recvfrom(4096)
            # Player count is at byte 31 in the A2S response
            return int(data[31])
        except Exception:
            return 0

class MinecraftProbe(BaseProbe):
    def get_player_count(self):
        # Implementation of Minecraft Ping on localhost:25565
        return 0

# Factory to pick the right one at runtime
def get_probe(game_type):
    probes = {
        'valheim': ValheimProbe,
        'minecraft': MinecraftProbe
    }
    return probes.get(game_type.lower(), BaseProbe)()