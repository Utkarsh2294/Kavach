"""
Kavach Backend — Pooled async Redis client.

Initialized once at app startup (via lifespan), shared across all requests.
Never reconnected per-request.

Key naming conventions:
  spend:{agent_id}:{window}     — rolling spend counter, TTL matching the window
  agent_status:{agent_id}       — 'active' | 'revoked', sub-millisecond read
  session:{session_id}          — auth session data (Phase 07 defines exact shape)
"""

import json
import redis.asyncio as aioredis
from app.config import get_settings


class RedisClient:
    """Pooled async Redis client singleton."""

    _pool: aioredis.Redis | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    @classmethod
    async def connect(cls) -> None:
        """Initialize the connection pool. Call once at app startup."""
        settings = get_settings()
        cls._pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )

    @classmethod
    async def disconnect(cls) -> None:
        """Close the connection pool. Call once at app shutdown."""
        if cls._pool:
            await cls._pool.aclose()
            cls._pool = None

    @classmethod
    def get_client(cls) -> aioredis.Redis:
        """Return the shared Redis client. Raises if not initialized."""
        if cls._pool is None:
            raise RuntimeError(
                "Redis not initialized. Call RedisClient.connect() first."
            )
        return cls._pool

    # ── Key helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def spend_key(agent_id: str, window: str) -> str:
        """Key for rolling spend counter: spend:{agent_id}:{window}"""
        return f"spend:{agent_id}:{window}"

    @staticmethod
    def agent_status_key(agent_id: str) -> str:
        """Key for agent status: agent_status:{agent_id}"""
        return f"agent_status:{agent_id}"

    @staticmethod
    def session_key(session_id: str) -> str:
        """Key for auth session: session:{session_id}"""
        return f"session:{session_id}"

    # ── Spend counter operations ─────────────────────────────────────────────

    @classmethod
    async def increment_spend(
        cls, agent_id: str, window: str, amount: float, ttl_seconds: int
    ) -> float:
        """Atomically increment an agent's spend counter for the given window."""
        r = cls.get_client()
        key = cls.spend_key(agent_id, window)
        pipe = r.pipeline()
        pipe.incrbyfloat(key, amount)
        pipe.expire(key, ttl_seconds, nx=True)  # Set TTL only if not already set
        results = await pipe.execute()
        return float(results[0])

    @classmethod
    async def get_spend(cls, agent_id: str, window: str) -> float:
        """Read an agent's current spend for the given window."""
        r = cls.get_client()
        val = await r.get(cls.spend_key(agent_id, window))
        return float(val) if val else 0.0

    # ── Agent status operations ──────────────────────────────────────────────

    @classmethod
    async def set_agent_status(cls, agent_id: str, status: str) -> None:
        """Set an agent's status ('active' | 'revoked')."""
        r = cls.get_client()
        await r.set(cls.agent_status_key(agent_id), status)

    @classmethod
    async def get_agent_status(cls, agent_id: str) -> str | None:
        """Read an agent's cached status. Returns None if not cached."""
        r = cls.get_client()
        return await r.get(cls.agent_status_key(agent_id))

    # ── Session operations ───────────────────────────────────────────────────

    @classmethod
    async def set_session(
        cls, session_id: str, data: dict, ttl_seconds: int = 1800
    ) -> None:
        """Store a session payload with TTL (default 30 min)."""
        r = cls.get_client()
        await r.set(
            cls.session_key(session_id), json.dumps(data), ex=ttl_seconds
        )

    @classmethod
    async def get_session(cls, session_id: str) -> dict | None:
        """Retrieve a session payload, or None if expired/missing."""
        r = cls.get_client()
        val = await r.get(cls.session_key(session_id))
        return json.loads(val) if val else None

    @classmethod
    async def delete_session(cls, session_id: str) -> None:
        """Delete a session (logout)."""
        r = cls.get_client()
        await r.delete(cls.session_key(session_id))
