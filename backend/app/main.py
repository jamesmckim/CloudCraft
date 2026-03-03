# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.api.routes import auth, servers, incidents, payments, internal # Import your new routers

app = FastAPI(title="CraftCloud API")

# Initialize database tables
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes
app.include_router(auth.router)

app.include_router(servers.router, prefix="/servers")
app.include_router(incidents.router, prefix="/servers")
app.include_router(internal.router, prefix="/internal/servers")
app.include_router(payments.router, prefix="/payments")

@app.get("/")
async def root():
    return {"message": "CraftCloud API is operational"}