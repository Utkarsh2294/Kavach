"""
Kavach Backend — FastAPI application entry point.

Wires up the lifespan (Redis connect/disconnect) and registers routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.redis_client import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    # Startup
    await RedisClient.connect()
    yield
    # Shutdown
    await RedisClient.disconnect()


app = FastAPI(
    title="Kavach API",
    description="Governance & Trust Layer for Autonomous Financial Agents",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health-check endpoint."""
    return {"status": "ok"}

from app.routes import agents, policies, transactions, escalations, audit

app.include_router(agents.router)
app.include_router(policies.router)
app.include_router(transactions.router)
app.include_router(escalations.router)
app.include_router(audit.router)
