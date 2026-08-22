"""Phase 09C sandbox fleet lifecycle.

Sandbox rows use the same tables as production data but are marked
``is_sandbox=True``.  Every fleet route and the websocket transport scope on
that flag, so synthetic data cannot appear in a real-data query (or vice
versa).  The three endpoints are deliberately idempotent enough for an
operator to practise the rogue-response flow repeatedly.
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_org_id, get_current_user_id, require_role
from app.models import Agent, AuditLog, Escalation, Transaction
from app.services.audit import write_audit
from app.services.cache import warm_agent
from app.services.transaction_pipeline import process_transaction

router = APIRouter(prefix="/api/v1/sandbox", tags=["Sandbox"])


async def _sandbox_agents(db: AsyncSession, org_id: UUID) -> list[Agent]:
    result = await db.execute(
        select(Agent).where(Agent.org_id == org_id, Agent.is_sandbox.is_(True))
    )
    return list(result.scalars().all())


async def _clear_sandbox(db: AsyncSession, org_id: UUID) -> None:
    """Delete only this org's synthetic rows, in FK dependency order."""
    agent_ids = select(Agent.id).where(
        Agent.org_id == org_id, Agent.is_sandbox.is_(True)
    )
    tx_ids = select(Transaction.id).where(Transaction.agent_id.in_(agent_ids))
    await db.execute(delete(Escalation).where(Escalation.transaction_id.in_(tx_ids)))
    await db.execute(delete(AuditLog).where(
        AuditLog.org_id == org_id, AuditLog.is_sandbox.is_(True)
    ))
    await db.execute(delete(Transaction).where(Transaction.agent_id.in_(agent_ids)))
    await db.execute(delete(Agent).where(
        Agent.org_id == org_id, Agent.is_sandbox.is_(True)
    ))
    await db.flush()


async def _create_fleet(db: AsyncSession, org_id: UUID) -> list[Agent]:
    """Create a deterministic 10-agent, three-level synthetic fleet."""
    root = Agent(org_id=org_id, name="Sandbox Treasury", type="procurement",
                 spend_cap_current=Decimal("100000"), trust_score=0.9,
                 is_sandbox=True)
    db.add(root)
    await db.flush()
    parents = [root]
    for index, (name, kind, cap) in enumerate((
        ("Sandbox Travel", "travel", "25000"),
        ("Sandbox Procurement", "procurement", "50000"),
        ("Sandbox Subscriptions", "subscription", "15000"),
    )):
        agent = Agent(org_id=org_id, name=name, type=kind,
                      parent_agent_id=root.id, spend_cap_current=Decimal(cap),
                      trust_score=0.8 - index * 0.03, is_sandbox=True)
        db.add(agent)
        parents.append(agent)
    await db.flush()
    for parent in parents[1:]:
        for suffix in ("A", "B"):
            db.add(Agent(org_id=org_id, name=f"{parent.name} {suffix}",
                         type="sub-agent", parent_agent_id=parent.id,
                         spend_cap_current=Decimal("7500"), trust_score=0.72,
                         is_sandbox=True))
    await db.flush()
    return await _sandbox_agents(db, org_id)


@router.post("/start", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("operator"))])
async def start_sandbox(
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    agents = await _sandbox_agents(db, org_id)
    created = not bool(agents)
    if created:
        agents = await _create_fleet(db, org_id)
        await write_audit(db, org_id, "sandbox_started", None,
                          {"agent_count": len(agents), "is_sandbox": True}, user_id,
                          is_sandbox=True)
    await db.commit()
    for agent in agents:
        await warm_agent(db, agent)
    return {"status": "started", "created": created, "agent_count": len(agents),
            "agent_ids": [str(agent.id) for agent in agents]}


@router.post("/reset", dependencies=[Depends(require_role("operator"))])
async def reset_sandbox(
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _clear_sandbox(db, org_id)
    agents = await _create_fleet(db, org_id)
    await write_audit(db, org_id, "sandbox_reset", None,
                      {"agent_count": len(agents), "is_sandbox": True}, user_id,
                      is_sandbox=True)
    await db.commit()
    for agent in agents:
        await warm_agent(db, agent)
    return {"status": "reset", "agent_count": len(agents),
            "agent_ids": [str(agent.id) for agent in agents]}


@router.post("/trigger-rogue", dependencies=[Depends(require_role("operator"))])
async def trigger_rogue(
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    agents = await _sandbox_agents(db, org_id)
    if not agents:
        raise HTTPException(status_code=409, detail="Start the sandbox before triggering rogue activity")
    rogue = next((agent for agent in agents if agent.parent_agent_id is not None), agents[0])
    spawned = []
    for index in range(2):
        agent = Agent(org_id=org_id, name=f"Unauthorized Sandbox Sub-agent {index + 1}",
                      type="sub-agent", parent_agent_id=rogue.id,
                      spend_cap_current=Decimal("1000"), trust_score=0.1,
                      status="active", is_sandbox=True)
        db.add(agent)
        spawned.append(agent)
    await db.flush()
    # A spike must be exercised through the normal pipeline, never injected
    # directly into the database, so policy/audit/feed behaviour is realistic.
    result = await process_transaction(
        db, org_id, rogue.id, float(rogue.spend_cap_current), "rogue_spike",
        actor_user_id=user_id, is_sandbox=True,
    )
    await write_audit(db, org_id, "sandbox_rogue_triggered", rogue.id,
                      {"spike_transaction_id": str(result.transaction.id),
                       "unauthorized_agent_ids": [str(agent.id) for agent in spawned],
                       "is_sandbox": True}, user_id, is_sandbox=True)
    await db.commit()
    for agent in spawned:
        await warm_agent(db, agent)
    return {"status": "triggered", "rogue_agent_id": str(rogue.id),
            "spike_transaction_id": str(result.transaction.id),
            "unauthorized_agent_ids": [str(agent.id) for agent in spawned]}
