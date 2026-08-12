# /fleet-manager/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import servers
from app.core.database import init_db
from app.models import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing fleet database...")
    await init_db()
    yield

app = FastAPI(
    title="Fleet Manager API",
    description="Microservice responsible for Kubernetes game server deployments.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with settings.DOMAIN_URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the server routes
app.include_router(servers.router, prefix="/servers")

@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint for Kubernetes/Docker."""
    return {"status": "healthy", "service": "fleet_manager"}