# Server Hosting Service

A kubernetes native game server hosting service.

### SET-UP

needs sops age key placed on host at: ~/.config/sops/age/keys.txt

### Troubleshooting (too many files open) (fswatchers)
make setup-host on root computer

## IP Address stupidness
in
deployments/k8s/overlays/local-dev/keycloak-ingress.yaml
deployments/k8s/overlays/local-dev/gateway.yaml
deployments/k8s/base/infra/keycloak/keycloak.yaml
deployments/k8s/base/infra/keycloak/realm-import.yaml

Makefile (setup-tls)


### Launching Dev Env

## (on host)
make setup-host

## (in dev container)
make setup-cluster

make dev --- <- limits fsnotify

local dev ip adress: https://app.[## host IP ##].nip.io:8443

(need to grant spoofed cert perm at this adress to login): https://sso.[## host IP ##].nip.io:8443/realms/craftcloud/.well-known/openid-configuration

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
