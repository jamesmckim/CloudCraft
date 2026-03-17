```mermaid
graph LR
    %% Definitions
    user[User]
    lb[ingress/loadbalancer]
    
    subgraph agones [Agones GameServer]
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

    subgraph Card Stack
        direction TB
        Card1[Card 1] ~~~ Card2[Card 2] ~~~ Card3[Card 3]
    end
    %% Connections and Protocols
    user --> lb
    lb -->|UDP| agones
    lb -.->|https| webui
    lb --> auth_billing
    
    agones --> webui
    webui --> telemetry
    webui --> fleet_manager
    
    auth_billing <--> db_main
    db_main <--> fleet_manager
    fleet_manager --> agones
    sidecar_list --> webui
