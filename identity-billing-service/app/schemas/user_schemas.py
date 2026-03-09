# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict

# --- User Authentication Schemas ---

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    username: str
    email: EmailStr
    credits: float
    
    # Allows Pydantic to read directly from your SQLAlchemy User model
    model_config = ConfigDict(from_attributes=True)

# --- Billing & Payment Schemas ---

class BuyRequest(BaseModel):
    package_id: str
    provider: str  # e.g., 'stripe' or 'paypal'