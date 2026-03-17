```mermaid
graph LR
    %% Definitions
    user[User]
    lb[ingress/loadbalancer]
    
    subgraph "Agones GameServer"
        %% Subgraph contains internal components
        direction TB
        game_server_list[Game Servers]
        sidecar_list[sidecar]
    end
    
    telemetry[telemetry service]
    webui[webui]
    auth_billing[auth billing]
    fleet_manager[fleet-manager]
    db_main[(Main Database)]
    db_session[(Game Session DB)]

    %% Connections and Protocols
    user --> lb
    lb -->|UDP| "Agones GameServer"
    lb -.->|https| webui
    lb --> auth_billing
    
    "Agones GameServer" --> webui
    webui --> telemetry
    webui --> fleet_manager
    
    auth_billing <--> db_main
    db_main <--> fleet_manager
    fleet_manager --> "Agones GameServer"
    sidecar_list --> webui
