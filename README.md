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

    %% Styling to approximate original colors and structure
    style user fill:#e1f5fe,stroke:#01579b
    style lb fill:#e1f5fe,stroke:#01579b
    style "Agones GameServer" fill:#f3e5f5,stroke:#4a148c
    style game_server_list fill:#ffffff,stroke:#333
    style sidecar_list fill:#ffffff,stroke:#333
    style telemetry fill:#e0f2f1,stroke:#004d40
    style webui fill:#e0f2f1,stroke:#004d40
    style auth_billing fill:#e0f2f1,stroke:#004d40
    style fleet_manager fill:#e0f2f1,stroke:#004d40
    style db_main fill:#e1f5fe,stroke:#01579b
    style db_session fill:#e1f5fe,stroke:#01579b
