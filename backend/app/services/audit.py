import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import AuditLog


GENESIS_HASH = "0" * 64


def canonical_payload(payload: dict) -> str:
    """Canonical serialization keeps the hash stable across processes."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def calculate_hash(prev_hash: str, payload: dict) -> str:
    return hashlib.sha256(f"{prev_hash}{canonical_payload(payload)}".encode("utf-8")).hexdigest()

async def write_audit(
    db: AsyncSession,
    org_id: uuid.UUID,
    event_type: str,
    agent_id: Optional[uuid.UUID],
    payload: dict,
    actor_user_id: Optional[uuid.UUID] = None,
    is_sandbox: bool = False,
) -> AuditLog:
    """
    Write an audit log entry.
    
    Phase 10D will add hash-chaining to this function's internals
    without changing any call site.
    
    Args:
        db: Database session
        org_id: Organization ID
        event_type: 'grant' | 'deny' | 'override' | 'revoke' | 'kill_switch'
        agent_id: Optional agent ID
        payload: JSON payload with event details
        actor_user_id: Optional user who performed the action
    """
    previous = (await db.execute(
        select(AuditLog)
        .where(AuditLog.org_id == org_id, AuditLog.is_sandbox == is_sandbox)
        .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .limit(1)
        .with_for_update()
    )).scalar_one_or_none()
    prev_hash = previous.this_hash if previous and previous.this_hash else GENESIS_HASH
    entry = AuditLog(
        org_id=org_id,
        event_type=event_type,
        agent_id=agent_id,
        actor_user_id=actor_user_id,
        payload=payload,
        prev_hash=prev_hash,
        this_hash=calculate_hash(prev_hash, payload),
        is_sandbox=is_sandbox,
    )
    db.add(entry)
    await db.flush()  # Get the ID assigned
    return entry
