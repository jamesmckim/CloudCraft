# Server Hosting Service

A nginx container frontend using a REST API to communicate with a python backend, that has access to a mongoDB, that launches a game server in a pod that is expossed to the internet.

```mermaid
flowchart LR
  U@{ shape: circle, label: "👤 User"}
  A@{ shape: rect, label: "Ingress controller" }
  B@{ shape: rect, label: "webui" }
  C@{ shape: rect, label: "Fleet-Manager" }
  G@{ shape: cyl, label: "mongoDB" }
  D@{ shape: rect, label: "Auth/Billing" }
  E@{ shape: rect, label: "Telemetry Service" }

  subgraph agones [Agones GameServer]
    direction TB
    F@{ shape: processes, label: "Game Servers" }
    S@{ shape: processes, label: "Sidecar" }
  end

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
