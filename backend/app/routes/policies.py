from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.deps import get_current_org_id, require_role
from app.models import Policy, Transaction, Agent
from app.schemas.policy import (
    PolicyCreate,
    PolicyUpdate,
    PolicyResponse,
    DryRunRequest,
    DryRunResponse,
    DryRunDiffItem
)
from app.services.rule_engine import evaluate_rules

router = APIRouter(prefix='/api/v1/policies', tags=['Policies'])

@router.get("", response_model=List[PolicyResponse])
async def get_policies(
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Policy).where(Policy.org_id == org_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role('operator'))])
async def create_policy(
    policy_data: PolicyCreate,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    db_policy = Policy(**policy_data.model_dump(), org_id=org_id)
    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)
    return db_policy

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Policy).where(Policy.id == policy_id, Policy.org_id == org_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.put("/{policy_id}", response_model=PolicyResponse, dependencies=[Depends(require_role('operator'))])
async def update_policy(
    policy_id: UUID,
    policy_update: PolicyUpdate,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Policy).where(Policy.id == policy_id, Policy.org_id == org_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    update_data = policy_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)
        
    await db.commit()
    await db.refresh(policy)
    return policy

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role('operator'))])
async def delete_policy(
    policy_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Policy).where(Policy.id == policy_id, Policy.org_id == org_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    await db.delete(policy)
    await db.commit()

@router.post("/{policy_id}/dry-run", response_model=DryRunResponse, dependencies=[Depends(require_role('operator'))])
async def dry_run_policy(
    policy_id: UUID,
    request: DryRunRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Policy).where(Policy.id == policy_id, Policy.org_id == org_id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Policy not found")
        
    # Load all transactions for this org
    tx_stmt = (
        select(Transaction, Agent)
        .join(Agent, Transaction.agent_id == Agent.id)
        .where(Agent.org_id == org_id)
    )
    tx_res = await db.execute(tx_stmt)
    tx_rows = tx_res.all()
    
    diff_items = []
    summary = {"newlyBlocked": 0, "newlyAllowed": 0, "unchanged": 0}
    
    # Build a mock policy-like object for the new conditions
    from dataclasses import dataclass, field as dc_field
    import uuid as _uuid

    @dataclass
    class _MockPolicy:
        id: _uuid.UUID
        name: str
        rule_json: dict
        priority: int
        active: bool

    # Wrap conditions: if multiple, use 'all'; if single, use directly
    if len(request.conditions) == 1:
        combined_rule = request.conditions[0]
    else:
        combined_rule = {"all": request.conditions}

    mock_policy = _MockPolicy(
        id=policy_id,
        name="Dry Run Policy",
        rule_json=combined_rule,
        priority=1,
        active=True,
    )
    
    for tx, agent in tx_rows:
        tx_dict = {
            "amount": float(tx.amount),
            "merchant_category": tx.merchant_category,
            "delegation_depth": 0,  # Simplified for dry-run
            "agent_type": agent.type,
            "time_of_day_hour": tx.timestamp.hour if tx.timestamp else 12,
        }
        result = evaluate_rules(tx_dict, [mock_policy])
        new_decision = "approve" if result.passed else "deny"
        
        orig_decision = tx.decision  # 'approve' | 'deny'
        
        triggered = orig_decision != new_decision
        
        if not triggered:
            summary["unchanged"] += 1
        elif orig_decision == "approve" and new_decision == "deny":
            summary["newlyBlocked"] += 1
        elif orig_decision == "deny" and new_decision == "approve":
            summary["newlyAllowed"] += 1
            
        if triggered:
            diff_items.append(
                DryRunDiffItem(
                    tx_id=str(tx.id),
                    agent_name=agent.name,
                    amount=float(tx.amount),
                    merchant_category=tx.merchant_category,
                    risk_score=tx.risk_score,
                    before=orig_decision,
                    after=new_decision,
                    triggered=True,
                )
            )
            
    return DryRunResponse(
        before_after_diff=diff_items,
        summary=summary,
    )

