# Server Hosting Service

A kubernetes native game server hosting service.

### SET-UP

needs sops age key placed on host at: ~/.config/sops/age/keys.txt

### Troubleshooting: "Too many open files" (fsnotify limit)

When running the Dev Container on a fresh Linux host (like Ubuntu), you may encounter this error from Uvicorn, Vite, or Skaffold:
`failed to create fsnotify watcher: too many open files`

This happens because modern IDEs (like VS Code) and hot-reloaders require more file watchers than the default Linux limit (8,192).

**To fix this permanently on the host machine:**

1. Open a terminal on the host machine (outside the Dev Container).
2. Run the following command to append the new limit to your system config:
   ```bash
   echo fs.file-max=524288 | sudo tee -a /etc/sysctl.conf
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   echo fs.inotify.max_user_instances=8192 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p


### Launching Dev Env

make setup-cluster

make dev --- <- limits fsnotify

local dev ip adress: https://app.127.0.0.1.nip.io:8443

(need to grant spoofed cert perm at this adress to login): https://sso.127.0.0.1.nip.io:8443/realms/craftcloud/.well-known/openid-configuration

May need to update inotify count: sudo sysctl -w fs.inotify.max_user_instances=8192
 

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
