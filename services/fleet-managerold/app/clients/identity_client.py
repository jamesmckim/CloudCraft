# /fleet-manager/app/clients/identity_client.py
import httpx
from fastapi import HTTPException

# from app.core.config import settings

class IdentityServiceClient:
    def __init__(self):
        self.base_url = "http://identity-service:5000"

    async def get_user_credits(self, user_id: str) -> float:
        """Fetches the user's credit balance from the Identity Service."""
        async with httpx.AsyncClient() as client:
            try:
                
                headers = {"X-User-ID": str(user_id)}
                
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/credits",
                    headers=headers
                )
                
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail="User not found in Identity Service.")
                
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Internal Auth Error: Missing X-User-ID header.")
                
                response.raise_for_status()
                data = response.json()
                return data.get("credits", 0.0)
                
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail="Identity service is currently unavailable.")