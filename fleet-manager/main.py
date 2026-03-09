# /main.py
from fastapi import FastAPI
from app.api.routes import servers
from app.core.database import engine, Base

# Create the database tables if they don't exist
# (In production, you should use Alembic for migrations instead of this)
from app.models import models
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fleet Manager API",
    description="Microservice responsible for Kubernetes game server deployments.",
    version="1.0.0"
)

# Register the server routes
app.include_router(servers.router, prefix="/api/servers")

@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint for Kubernetes/Docker."""
    return {"status": "healthy", "service": "fleet_manager"}