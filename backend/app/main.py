"""
Kavach Backend — FastAPI application entry point.

Production lifecycle:
  startup  -> warm ML ModelRegistry (load artifacts once, zero net calls)
           -> connect Redis (graceful: app starts even with Redis down)
           -> warm the agent status/cap Redis cache from the DB
  shutdown -> close the Redis pool

Routers registered here are the single inclusion point for every phase.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.redis_client import RedisClient
from app.services.scoring import ModelRegistry

logger = logging.getLogger("kavach.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. ML risk models load once at startup — in-process scoring, zero net calls.
    ModelRegistry.load()
    if not ModelRegistry.is_ready():
        logger.warning(
            "ML artifacts not loaded (flags missing or ml_enabled=False); "
            "scoring degrades to rule-engine-only. Governance is unaffected."
        )
    else:
        logger.info("ML artifacts loaded (IsolationForest + XGBoost).")

    # 2. Redis — graceful: connect if available, never crash the app on it.
    try:
        await RedisClient.connect()
        # Warm the cached status/cap for every agent so the spend-cap Lua gate
        # is authoritative from the very first request, not after a cache miss.
        try:
            from app.database import async_session_factory
            from app.services.cache import warm_all_agents
            async with async_session_factory() as db:
                await warm_all_agents(db)
        except Exception as exc:  # pragma: no cover - resilience path
            logger.warning("agent-cache warm failed: %s", exc)
    except Exception as exc:
        logger.warning("Redis unavailable at startup: %s. Spend-cap gate will "
                       "degrade to DB-status backstop only until Redis recovers.", exc)

    yield

    try:
        await RedisClient.disconnect()
    except Exception:  # pragma: no cover
        pass


app = FastAPI(
    title="Kavach API",
    description="Governance & Trust Layer for Autonomous Financial Agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health-check — reflects real infra connectivity, not just process state."""
    return {
        "status": "ok",
        "ml_ready": ModelRegistry.is_ready(),
        "redis_ready": RedisClient._pool is not None,
    }


from app.routes import agents, policies, transactions, escalations, audit, auth, ws, sandbox  # noqa: E402

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(policies.router)
app.include_router(transactions.router)
app.include_router(escalations.router)
app.include_router(audit.router)
app.include_router(ws.router)
app.include_router(sandbox.router)
