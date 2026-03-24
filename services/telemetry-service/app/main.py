# /telemetry-service/app/main.py
import contextlib
from fastapi import FastAPI
from app.api.routes import incidents, internal
from app.core.database import engine, Base

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # This block executes right before the server starts
    async with engine.begin() as conn:
        # We use run_sync to execute the synchronous create_all command safely
        await conn.run_sync(Base.metadata.create_all)
    
    yield # The server is now running and accepting requests
    
    # Optional: Any shutdown logic would go here
    await engine.dispose()
    
app = FastAPI(title="Telemetry & Incident Microservice", lifespan=lifespan)

app.include_router(internal.router, prefix="/internal")
app.include_router(incidents.router, prefix="/incidents")

@app.get("/health")
def health_check():
    return {"status": "ok"}