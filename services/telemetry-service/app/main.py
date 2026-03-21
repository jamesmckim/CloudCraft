# /telemetry-service/app/main.py
from fastapi import FastAPI
from app.api.routes import incidents, internal
from app.core.database import engine, Base

# Create tables (In production, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Telemetry & Incident Microservice")

app.include_router(internal.router, prefix="/internal")
app.include_router(incidents.router, prefix="/incidents")

@app.get("/health")
def health_check():
    return {"status": "ok"}