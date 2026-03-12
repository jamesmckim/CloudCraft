# /telemetry-service/app/core/auth.py
from fastapi import Header, HTTPException, status, Depends
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# --- 1. External User Auth (Via Traefik Gateway) ---
async def get_current_user_stateless(
    x_user_id: str = Header(None, alias="X-User-ID")
) -> str:
    """
    Extracts the user ID injected by the Traefik API Gateway.
    Replaces the old JWT decoding logic, meaning the Telemetry service 
    no longer needs to share the JWT_SECRET.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing identity context"
        )
    return x_user_id

# --- 2. Internal Sidecar Auth (Via K8s Service Account Tokens) ---
# Initialize the Kubernetes client to talk to the TokenReview API
try:
    config.load_incluster_config()
    auth_v1 = client.AuthenticationV1Api()
except config.ConfigException:
    auth_v1 = None # Fallback for local development outside the cluster

async def verify_sidecar_token(authorization: str = Header(None)):
    """
    Validates the Kubernetes Service Account token injected into the Game Sidecar.
    Used by internal metric ingestion routes.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing sidecar token")
    
    token = authorization.split(" ")[1]

    if not auth_v1:
        # Failsafe for local testing
        return "local-dev-sidecar"

    token_review = client.V1TokenReview(
        spec=client.V1TokenReviewSpec(token=token)
    )

    try:
        response = auth_v1.create_token_review(token_review)
        
        if not response.status.authenticated:
            raise HTTPException(status_code=401, detail="Invalid Kubernetes token")
            
        # Ensure the token belongs specifically to your Agones game servers
        sa_name = response.status.user.username
        if sa_name != "system:serviceaccount:default:game-server-sa":
            raise HTTPException(status_code=403, detail="Unauthorized service account")
            
        return sa_name

    except ApiException:
        raise HTTPException(status_code=500, detail="Failed to communicate with K8s API")