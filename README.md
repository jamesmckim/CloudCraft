# Server Hosting Service

########### SET-UP ##############3

needs sops age key placed on host at: ~/.config/aops/age/keys.txt

local dev ip adress: https://app.127.0.0.1.nip.io:8443

(need to grant spoofed cert perm at this adress to login): https://sso.127.0.0.1.nip.io:8443/realms/craftcloud/.well-known/openid-configuration

May need to update inotify count: sudo sysctl -w fs.inotify.max_user_instances=8192

A kubernetes native game server hosting service. 

```mermaid
flowchart LR
  U@{ shape: circle, label: "👤 User"}
  A@{ shape: rect, label: "Ingress controller" }
  B@{ shape: rect, label: "webui" }

  subgraph agones [Agones GameServer]
    direction TB
    F@{ shape: processes, label: "Game Servers" }
    S@{ shape: processes, label: "Sidecar" }
  end
  
  D@{ shape: rect, label: "Auth/Billing" }
  G@{ shape: cyl, label: "mongoDB" }
  C@{ shape: rect, label: "Fleet-Manager"}
  E@{ shape: rect, label: "Telemetry Service" }



A --> |HTTP| B;
A <--> |UDP| F;
B --> C;
B --> D;
B --> E;
C --> agones;
C <--> G;
D <--> G;
S --> E;
U -.-> A;
