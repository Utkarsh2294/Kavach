"""
Kavach Backend — Pooled async Redis client.

Initialized once at app startup (via lifespan), shared across all requests.
Never reconnected per-request.

Key naming conventions:
  spend:{agent_id}:{window}     — rolling spend counter, TTL = window
  agent_status:{agent_id}      — 'active' | 'revoked', sub-millisecond read
  agent_cap:{agent_id}         — cached spend_cap_current (hot-path cap check)
  session:{session_id}         — auth session data (Phase 07 defines shape)
  feed:{org_id}:live            — pub/sub channel for real-org WS feed
  feed:{org_id}:sandbox         — pub/sub channel for sandbox WS feed
"""

import json
import uuid
import redis.asyncio as aioredis
from app.config import get_settings


# ── Atomic spend-cap enforcement Lua (Phase 09A) ───────────────────────────
# Runs entirely inside one Redis EVAL so the GET-status → GET-cap → INCR-check
# sequence is atomic — concurrent transactions for the same agent cannot
# double-spend past the cap (a GET-then-SET in Python would race).
SPEND_RESERVE_LUA = """
local status = redis.call('GET', KEYS[2])
if status == 'revoked' then
  return {0, 'revoked'}
end
local cap = tonumber(redis.call('GET', KEYS[3]) or '0')
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local amount = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
local newval = current + amount
if cap ~= nil and cap > 0 and newval > cap then
  return {0, 'spend_cap_exceeded'}
end
local existed = redis.call('EXISTS', KEYS[1])
local nv = string.format('%.6f', newval)
redis.call('SET', KEYS[1], nv)
if existed == 0 and ttl > 0 then
  redis.call('EXPIRE', KEYS[1], ttl)
end
return {1, 'ok'}
"""


class RedisClient:
    """Pooled async Redis client singleton."""

    _pool: aioredis.Redis | None = None
    _spend_script = None  # registered script handle for the Lua exploit above

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
        # Register the spend-reserve Lua script once (zero per-call eval setup).
        cls._spend_script = cls._pool.register_script(SPEND_RESERVE_LUA)

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

    @staticmethod
    def agent_cap_key(agent_id: str) -> str:
        """Key for cached spend cap: agent_cap:{agent_id}"""
        return f"agent_cap:{agent_id}"

    @staticmethod
    def feed_channel(org_id: str, sandbox: bool = False) -> str:
        """Pub/sub channel for real-time WebSocket fanout per org/sandbox."""
        return f"feed:{org_id}:sandbox" if sandbox else f"feed:{org_id}:live"

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

    # ── Spend cap cache operations ───────────────────────────────────────

    @classmethod
    async def set_agent_cap(cls, agent_id: str, cap: float) -> None:
        """Cache an agent's spend_cap_current for hot-path enforcement."""
        r = cls.get_client()
        await r.set(cls.agent_cap_key(agent_id), float(cap))

    @classmethod
    async def get_agent_cap(cls, agent_id: str) -> float | None:
        """Read cached cap. Returns None if not cached (caller may fallback)."""
        r = cls.get_client()
        val = await r.get(cls.agent_cap_key(agent_id))
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    @classmethod
    async def delete_agent(cls, agent_id: str) -> None:
        """Drop status + cap cache for an agent (after deletion / lifecycle)."""
        r = cls.get_client()
        await r.delete(cls.agent_status_key(agent_id), cls.agent_cap_key(agent_id))

    # ── Atomic spend enforcement (Phase 09A) ──────────────────────────────

    @classmethod
    async def check_and_reserve_spend(
        cls, agent_id: str, amount: float, window_seconds: int = 3600
    ) -> tuple[bool, str]:
        """
        Atomically check agent status + cap, then reserve `amount` against the
        rolling spend counter. Returns (allowed: bool, reason: str).

        'revoked'        -> (False, 'revoked')            (no counter touched)
        cap exceeded     -> (False, 'spend_cap_exceeded')
        approved         -> (True, 'ok')

        Implemented as a single Lua EVAL — the GET-then-SET is atomic inside the
        script, so concurrent calls for the same agent cannot double-spend.
        """
        if cls._spend_script is None:
            raise RuntimeError("Spend script not registered (call RedisClient.connect).")
        keys = [
            cls.spend_key(agent_id, "rolling"),
            cls.agent_status_key(agent_id),
            cls.agent_cap_key(agent_id),
        ]
        result = await cls._spend_script(keys=keys, args=[float(amount), int(window_seconds)])
        # redis-py returns the Lua table as a list of str
        ok = str(result[0]) == "1"
        reason = str(result[1])
        return ok, reason

    # ── Real-time feed pub/sub (Phase 09B) ───────────────────────────────

    @classmethod
    async def publish_feed(cls, org_id: str, sandbox: bool, message: dict) -> None:
        """Publish a WS feed message to the org/sandbox pub/sub channel."""
        r = cls.get_client()
        await r.publish(cls.feed_channel(str(org_id), sandbox), json.dumps(message, default=str))

    @classmethod
    def feed_pubsub(cls, org_id: str, sandbox: bool = False):
        """Return a pubsub object subscribed to the org/sandbox feed channel."""
        r = cls.get_client()
        pubsub = r.pubsub()
        return pubsub, cls.feed_channel(str(org_id), sandbox)
