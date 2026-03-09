# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routers import auth, payments

# --- Lifespan Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database tables
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    yield
    # Shutdown logic can go here if needed
    print("Shutting down Identity & Billing Service...")

# --- App Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Microservice for User Authentication and Billing",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Configuration ---
# Allow your frontend domain (e.g., localhost:3000) to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.DOMAIN_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router Registration ---
# We use prefixes here to keep the API URLs clean and organized
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(payments.router, prefix="/api/v1/payments")

@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint for load balancers or container orchestration."""
    return {"status": "ok", "service": settings.PROJECT_NAME}