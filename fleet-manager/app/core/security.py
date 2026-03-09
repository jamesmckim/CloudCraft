# /app/core/security.py
import os
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# This MUST match the secret key used by your Identity Service
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not found! The server cannot start safely.")

ALGORITHM = "HS256"

# Points to the Identity Service token URL for Swagger UI compatibility
IDENTITY_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8000")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{IDENTITY_URL}/token")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Validates the JWT and extracts the user ID."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception