"""
Phase 09B — real-time WebSocket feed message builders.

The shapes produced here are the binding real-time contract the frontend
emailed in `frontend/src/mocks/livedata-contract.md`. They MUST match
byte-for-byte so Phase 11 swapping the mock generator for a real WebSocket
is a one-line client change.

Envelope:  {"type": <str>, "payload": <obj>}
All field names are lowerCamelCase. riskScore/trustScore are integers 0..100.
cap / totalSpend are floats (USD). timestamp is float epoch seconds.
graph_snapshot node shape uses `agentType` (NOT `type`). cap must stay > 0.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models import Agent, Transaction
from app.redis_client import RedisClient
from app.services.scoring import score_to_credit_0_100


def _epoch_seconds(dt: datetime) -> float:
    if dt is None:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _trust_to_0_100(trust_0_1: float) -> int:
    return int(round(max(0.0, min(1.0, float(trust_0_1 or 0.0))) * 100))


def _cap_float(agent: Agent) -> float:
    """Cap as a float, never 0 (the dashboard divides by it)."""
    cap = float(agent.spend_cap_current or 0.0)
    return cap if cap > 0 else 1.0


# ── Message builders (pure — testable without infra) ─────────────────────


def transaction_update(
    agent: Agent,
    transaction: Transaction,
    risk_score_0_1: Optional[float],
) -> dict:
    return {
        "type": "transaction_update",
        "payload": {
            "id": str(transaction.id),
            "agentId": str(agent.id),
            "agentName": agent.name,
            "amount": float(transaction.amount),
            "merchantCategory": transaction.merchant_category,
            "decision": transaction.decision,
            "riskScore": score_to_credit_0_100(risk_score_0_1) if risk_score_0_1 is not None else 0,
            "timestamp": _epoch_seconds(transaction.timestamp),
        },
    }


def agent_status_update(agent: Agent, total_spend: float) -> dict:
    return {
        "type": "agent_status_update",
        "payload": {
            "agentId": str(agent.id),
            "trustScore": _trust_to_0_100(agent.trust_score),
            "active": (agent.status == "active"),
            "cap": _cap_float(agent),
            "totalSpend": float(total_spend or 0.0),
        },
    }


def trust_score_update(agent: Agent) -> dict:
    return {
        "type": "trust_score_update",
        "payload": {
            "agentId": str(agent.id),
            "trustScore": _trust_to_0_100(agent.trust_score),
        },
    }


async def graph_snapshot_for_agents(agents: list, sandbox: bool = False) -> dict:
    """
    Build a full delegation-tree snapshot. `agents` is an iterable of Agent
    ORM rows (already scoped to one org). totalSpend is read from Redis.
    """
    nodes = []
    edges = []
    for a in agents:
        spend = 0.0
        try:
            spend = await RedisClient.get_spend(str(a.id), "rolling")
        except Exception:
            spend = 0.0
        nodes.append({
            "id": str(a.id),
            "name": a.name,
            "agentType": a.type,
            "trustScore": _trust_to_0_100(a.trust_score),
            "active": (a.status == "active"),
            "cap": _cap_float(a),
            "totalSpend": float(spend or 0.0),
            "parentId": str(a.parent_agent_id) if a.parent_agent_id else None,
        })
        if a.parent_agent_id is not None:
            edges.append({
                "id": f"e_{a.parent_agent_id}_{a.id}",
                "source": str(a.parent_agent_id),
                "target": str(a.id),
            })
    return {"type": "graph_snapshot", "payload": {"nodes": nodes, "edges": edges}}


# ── Publish helper (itched through Redis pub/sub for cross-worker fanout) ──


async def publish_feed_event(org_id, sandbox: bool, message: dict) -> None:
    """Publish a WS feed message to the org/sandbox pub/sub channel."""
    await RedisClient.publish_feed(str(org_id), bool(sandbox), message)
