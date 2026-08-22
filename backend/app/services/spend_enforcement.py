"""
Phase 09A — Redis-backed spend-cap enforcement.

Inserted as the FIRST step of `process_transaction()` (before the rule engine
or ML scorer ever run): a revoked agent or a maxed-out cap short-circuits to
a deny, so neither the rule engine nor the ML model is consulted.

`check_and_reserve_spend` is implemented atomically via a single Redis Lua
EVAL (see `redis_client.SPEND_RESERVE_LUA`). The GET-status → GET-cap →
INCR-check-then-SET sequence runs inside one Lua invocation, so concurrent
transactions for the same agent cannot double-spend past the cap.

Cap caching: the Lua read of `agent_cap:{agent_id}` requires the cap to be in
Redis. The pipeline caches `Agent.spend_cap_current` before calling, and the
startup hook `warm_agent_cache()` pre-loads every agent's status + cap. If the
cap is missing the guard degrades to "no cap enforced" for that call (the
status check still applies), so governance never hard-fails on a cache miss.
"""

from dataclasses import dataclass

from app.redis_client import RedisClient


@dataclass
class ReserveResult:
    allowed: bool
    reason: str

    def __bool__(self) -> bool:  # allows `if check_and_reserve_spend(...):`
        return self.allowed


async def check_and_reserve_spend(
    agent_id: str, amount: float, window: str = "1h"
) -> ReserveResult:
    """
    Atomically check agent status + cap and reserve `amount` against the
    rolling spend counter.

    Returns a ReserveResult:
        (False, 'revoked')             — agent is revoked (counter untouched)
        (False, 'spend_cap_exceeded')  — would exceed the cached cap
        (True,  'ok')                  — reserved
    """
    window_seconds = 3600 if window in ("1h", "rolling") else int(window)
    ok, reason = await RedisClient.check_and_reserve_spend(
        str(agent_id), float(amount), int(window_seconds)
    )
    return ReserveResult(allowed=bool(ok), reason=reason)


async def release_spend(agent_id: str, amount: float) -> None:
    """Refund a reservation on a downstream deny/escalate (keeps counter honest)."""
    try:
        from app.redis_client import RedisClient as _R
        key = _R.spend_key(str(agent_id), "rolling")
        r = _R.get_client()
        await r.incrbyfloat(key, -float(amount))
    except Exception:
        # Refund is best-effort; never let it mask the original error.
        pass
