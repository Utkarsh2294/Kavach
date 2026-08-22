"""
Phase 09 — agent-status / spend-cap Redis cache warming.

The spend-cap enforcement Lua (redis_client.SPEND_RESERVE_LUA) reads
`agent_status:{id}` and `agent_cap:{id}` from Redis, so those keys MUST be
populated for the hot path to enforce anything. This module warms them at
startup (every agent) and exposes per-mutation updaters the routes call on
agent create / cap change / kill-switch — keeping the cache and the DB in lock
step without a per-request read-back.

Degradation: if Redis is unavailable the warmers log and continue; the DB
remains the source of truth and `process_transaction` carries a DB-level
revoked-status backstop so a revoked agent is never approved even with Redis
down.
"""

from __future__ import annotations

import logging
from typing import Iterable
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent
from app.redis_client import RedisClient

logger = logging.getLogger("kavach.cache")


async def warm_agent(db: AsyncSession, agent: Agent) -> None:
    """Push one agent's status + cap into Redis."""
    try:
        await RedisClient.set_agent_status(str(agent.id), agent.status)
        await RedisClient.set_agent_cap(str(agent.id), float(agent.spend_cap_current or 0))
    except Exception as exc:  # pragma: no cover - resilience path
        logger.warning("warm_agent(%s) failed: %s", agent.id, exc)


async def warm_all_agents(db: AsyncSession) -> int:
    """Warm the Redis cache for every agent in the fleet (startup hook)."""
    res = await db.execute(select(Agent))
    agents: Iterable[Agent] = res.scalars().all()
    n = 0
    for a in agents:
        await warm_agent(db, a)
        n += 1
    if n:
        logger.info("warmed %d agents into Redis cache", n)
    return n


async def refresh_status(agent_id, status: str) -> None:
    """Call after a status change (kill switch / revive / lifecycle)."""
    try:
        await RedisClient.set_agent_status(str(agent_id), status)
    except Exception as exc:  # pragma: no cover
        logger.warning("refresh_status(%s) failed: %s", agent_id, exc)


async def refresh_cap(agent_id, cap) -> None:
    """Call after a cap change (agent update / escalation adjust_cap)."""
    try:
        await RedisClient.set_agent_cap(str(agent_id), float(cap or 0))
    except Exception as exc:  # pragma: no cover
        logger.warning("refresh_cap(%s) failed: %s", agent_id, exc)


async def evict_agent(agent_id) -> None:
    """Drop cached status + cap after an agent is deleted."""
    try:
        await RedisClient.delete_agent(str(agent_id))
    except Exception as exc:  # pragma: no cover
        logger.warning("evict_agent(%s) failed: %s", agent_id, exc)
