# /fleet-manager/app/core/security.py
from fastapi import Header, HTTPException, status

async def get_current_user_id(
    x_user_id: str = Header(None, alias="X-User-ID")
) -> str:
    """
    Extracts the user ID injected by the Traefik API Gateway after successful ForwardAuth.
    Bypasses token decoding entirely.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing identity context"
        )
    return x_user_id