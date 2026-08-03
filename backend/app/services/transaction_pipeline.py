import uuid
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, Policy, Transaction, Escalation
from app.services.rule_engine import evaluate_rules, RuleResult
from app.services.audit import write_audit

@dataclass
class TransactionResult:
    transaction: Transaction
    rule_result: RuleResult
    escalation: Optional[Escalation] = None

def compute_delegation_depth(agent: Agent) -> int:
    """
    Compute the delegation depth of an agent by walking up the parent chain.
    This is computed in-memory since we eagerly load parent relationships.
    For the seed data: Treasury=0, Travel/Subscription/Procurement=1, Hotel/Flight/Office/IT=2
    """
    depth = 0
    current = agent
    while current.parent_agent_id is not None:
        depth += 1
        if hasattr(current, 'parent_agent') and current.parent_agent is not None:
            current = current.parent_agent
        else:
            break
    return depth

async def process_transaction(
    db: AsyncSession,
    org_id: uuid.UUID,
    agent_id: uuid.UUID,
    amount: float,
    merchant_category: str,
    actor_user_id: Optional[uuid.UUID] = None,
) -> TransactionResult:
    """
    Process a transaction through the full pipeline.
    
    Pipeline stages (structured for later phase insertions):
    1. Load agent (verify exists and is active)
    2. [Phase 09 inserts Redis spend-limit check here]
    3. Evaluate rules against all active policies
    4. [Phase 08 inserts ML risk scoring here]
    5. Write transaction row
    6. Write audit log row
    7. If escalated, create escalation queue entry
    
    Returns:
        TransactionResult with the saved transaction, rule evaluation, and optional escalation
    """
    # 1. Load agent with parent chain for delegation depth
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.parent_agent))
        .where(Agent.id == agent_id, Agent.org_id == org_id)
    )
    agent = result.scalar_one_or_none()
    if agent is None:
        raise ValueError(f"Agent {agent_id} not found")
    if agent.status == 'revoked':
        raise ValueError(f"Agent {agent_id} is revoked")
    
    # Load full parent chain for delegation depth calculation
    # Walk up manually since selectinload only gets one level
    current = agent
    depth = 0
    while current.parent_agent_id is not None:
        parent_result = await db.execute(
            select(Agent).where(Agent.id == current.parent_agent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if parent is None:
            break
        current.parent_agent = parent
        current = parent
        depth += 1
    
    # Build transaction context dict for the rule engine
    now = datetime.now(timezone.utc)
    tx_context = {
        'amount': float(amount),
        'merchant_category': merchant_category,
        'delegation_depth': depth,
        'agent_type': agent.type,
        'time_of_day_hour': now.hour,
    }
    
    # 2. [Phase 09: Redis spend-limit check goes here]
    
    # 3. Evaluate rules
    policies_result = await db.execute(
        select(Policy).where(Policy.org_id == org_id, Policy.active == True)
    )
    policies = list(policies_result.scalars().all())
    rule_result = evaluate_rules(tx_context, policies)
    
    # 4. [Phase 08: ML risk scoring goes here]
    
    # Determine decision
    decision = 'approve' if rule_result.passed else 'deny'
    
    # Generate a delegation chain ID (groups transactions in same delegation chain)
    # For now, use a new UUID per transaction
    delegation_chain_id = uuid.uuid4()
    
    # 5. Write transaction row
    tx = Transaction(
        agent_id=agent_id,
        amount=Decimal(str(amount)),
        merchant_category=merchant_category,
        decision=decision,
        risk_score=None,  # Phase 08 fills this
        triggered_rule_id=rule_result.denied_by.id if rule_result.denied_by else None,
        delegation_chain_id=delegation_chain_id,
    )
    db.add(tx)
    await db.flush()
    
    # 6. Write audit log
    event_type = 'grant' if decision == 'approve' else 'deny'
    await write_audit(
        db=db,
        org_id=org_id,
        event_type=event_type,
        agent_id=agent_id,
        payload={
            'transaction_id': str(tx.id),
            'amount': float(amount),
            'merchant_category': merchant_category,
            'decision': decision,
            'evaluation_trace': rule_result.evaluation_trace,
        },
        actor_user_id=actor_user_id,
    )
    
    # 7. Handle escalation (not implemented in this phase but structure is ready)
    escalation = None
    
    return TransactionResult(
        transaction=tx,
        rule_result=rule_result,
        escalation=escalation,
    )
