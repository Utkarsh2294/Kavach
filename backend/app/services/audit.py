import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog

async def write_audit(
    db: AsyncSession,
    org_id: uuid.UUID,
    event_type: str,
    agent_id: Optional[uuid.UUID],
    payload: dict,
    actor_user_id: Optional[uuid.UUID] = None,
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
    entry = AuditLog(
        org_id=org_id,
        event_type=event_type,
        agent_id=agent_id,
        actor_user_id=actor_user_id,
        payload=payload,
        prev_hash=None,  # Phase 10D implements hash-chaining
        this_hash=None,
    )
    db.add(entry)
    await db.flush()  # Get the ID assigned
    return entry
