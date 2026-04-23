# /identity-billing-service/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from arq import create_pool
from arq.connections import RedisSettings
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routers import auth, payments, users, internal

# --- Lifespan Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database tables
    print("Initializing database...")
    await init_db()
    print("Database initialized.")
    
    print("Connecting to Redis...")
    app.state.redis = await create_pool(RedisSettings(
        host=settings.REDIS_URL,
        port=6379,
        password=settings.REDIS_PASSWORD
    ))
    yield
    
    print("Shutting down...")
    app.state.redis.close()
    await app.state.redis.aclose()

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
app.include_router(auth.router, prefix="/auth")
app.include_router(payments.router, prefix="/payments")
app.include_router(users.router, prefix="/users")
app.include_router(internal.router, prefix="/internal")

@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint for load balancers or container orchestration."""
    return {"status": "ok", "service": settings.PROJECT_NAME}