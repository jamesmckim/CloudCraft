# Server Hosting Service

A nginx container frontend using a REST API to communicate with a python backend, that has access to a mongoDB, that launches a game server in a pod that is expossed to the internet.

```mermaid
flowchart LR
  A@{ shape: rect, label: "Ingress controller" }
  B@{ shape: rect, label: "webui" }
  C@{ shape: rect, label: "Fleet-Manager" }
  D@{ shape: rect, label: "Auth/Billing" }
  E@{ shape: rect, label: "Telemetry Service" }
  F@{ shape: processes, label: "Gamer Servers" }
  G@{ shape: cyl, label: "mongoDB" }
  H@{ shape: cloud, label: "internet" }
  U@{ shape: circle, label: "👤 User"}
A --> |HTTP| B;
A <--> |UDP| H;
A <-.- U;
B --> C;
B --> D;
B --> E;
C --> F;
C <--> G;
D <--> G;
E <-- F;
