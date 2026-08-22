from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from app.database import get_db
from app.deps import get_current_org_id, get_current_user_id, require_role
from app.schemas.escalation import EscalationResponse, EscalationAction, EscalationActionResponse
from app.models import Escalation, Transaction, Agent
from app.services.audit import write_audit
from app.services.cache import refresh_cap

router = APIRouter(prefix='/api/v1/escalations', tags=['Escalations'])

@router.get("", response_model=dict)
async def get_escalations(
    sandbox: bool = False,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Escalation, Transaction, Agent)
        .join(Transaction, Escalation.transaction_id == Transaction.id)
        .join(Agent, Transaction.agent_id == Agent.id)
        .where(Agent.org_id == org_id, Agent.is_sandbox == sandbox)
    )
    result = await db.execute(stmt)
    
    items = []
    for esc, tx, agent in result.all():
        items.append({
            "id": str(esc.id),
            "transactionId": str(tx.id),
            "agentName": agent.name,
            "amount": float(tx.amount),
            "merchantCategory": tx.merchant_category,
            "riskScore": tx.risk_score,
            "status": esc.status,
            "reviewedBy": str(esc.reviewer_id) if esc.reviewer_id else None,
            "reviewedAt": esc.reviewed_at.isoformat() if esc.reviewed_at else None,
        })
        
    return {"items": items}

@router.post("/{escalation_id}", response_model=EscalationActionResponse, dependencies=[Depends(require_role('reviewer'))])
async def process_escalation(
    escalation_id: UUID,
    action_data: EscalationAction,
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Escalation, Transaction, Agent)
        .join(Transaction, Escalation.transaction_id == Transaction.id)
        .join(Agent, Transaction.agent_id == Agent.id)
        .where(Escalation.id == escalation_id, Agent.org_id == org_id, Agent.is_sandbox == sandbox)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Escalation not found")
        
    esc, tx, agent = row
    
    esc.reviewer_id = user_id
    esc.reviewed_at = datetime.now(timezone.utc)

    if action_data.action == 'approve':
        esc.status = 'approved'
        tx.decision = 'approved'
    elif action_data.action == 'deny':
        esc.status = 'denied'
        tx.decision = 'denied'
    elif action_data.action == 'adjust_cap':
        esc.status = 'adjusted'
        if action_data.adjusted_cap_amount is not None:
            agent.spend_cap_current = Decimal(str(action_data.adjusted_cap_amount))
            await refresh_cap(agent.id, agent.spend_cap_current)
    else:
        raise HTTPException(status_code=400, detail="Unrecognized action")
            
    await write_audit(
        db=db,
        org_id=org_id,
        event_type="escalation_reviewed",
        agent_id=agent.id,
        payload={"escalation_id": str(esc.id), "action": action_data.action},
        actor_user_id=user_id
    )
    
    await db.commit()
    return EscalationActionResponse(
        id=esc.id,
        status=esc.status,
        reviewed_at=esc.reviewed_at,
    )
