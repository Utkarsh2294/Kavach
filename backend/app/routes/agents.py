import time
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.deps import get_current_org_id, get_current_user_id, require_role
from app.models import Agent, Transaction
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse,
    KillSwitchResponse, SimulateExposureRequest, SimulateExposureResponse,
)
from app.services.audit import write_audit
from app.services.cache import warm_agent, refresh_status, refresh_cap, evict_agent
from app.redis_client import RedisClient

router = APIRouter(prefix='/api/v1/agents', tags=['Agents'])


def _scope(stmt, org_id, sandbox: bool):
    """Apply the org + real/sandbox scoping every fleet query must respect."""
    return stmt.where(Agent.org_id == org_id, Agent.is_sandbox == sandbox)


@router.get("", response_model=List[AgentResponse])
async def get_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    sandbox: bool = Query(False, description="Show sandbox agents instead of real"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = _scope(select(Agent), org_id, sandbox)
    if status_filter:
        stmt = stmt.where(Agent.status == status_filter)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role('operator'))])
async def create_agent(
    agent_data: AgentCreate,
    sandbox: bool = Query(False),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    if agent_data.parent_agent_id:
        parent_stmt = _scope(select(Agent), org_id, sandbox).where(Agent.id == agent_data.parent_agent_id)
        parent_res = await db.execute(parent_stmt)
        if not parent_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent agent not found or belongs to a different organization/sandbox")

    db_agent = Agent(**agent_data.model_dump(), org_id=org_id, is_sandbox=sandbox)
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    await warm_agent(db, db_agent)
    return db_agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    sandbox: bool = Query(False),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = _scope(select(Agent), org_id, sandbox).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse,
            dependencies=[Depends(require_role('operator'))])
async def update_agent(
    agent_id: UUID,
    agent_update: AgentUpdate,
    sandbox: bool = Query(False),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = _scope(select(Agent), org_id, sandbox).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent_update.model_dump(exclude_unset=True)
    cap_changed = "spend_cap_current" in update_data
    for key, value in update_data.items():
        setattr(agent, key, value)

    await db.commit()
    await db.refresh(agent)
    await warm_agent(db, agent)  # status or cap may have changed -> refresh both
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role('operator'))])
async def delete_agent(
    agent_id: UUID,
    sandbox: bool = Query(False),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = _scope(select(Agent), org_id, sandbox).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    child_stmt = _scope(select(Agent), org_id, sandbox).where(Agent.parent_agent_id == agent_id)
    if (await db.execute(child_stmt)).first():
        raise HTTPException(status_code=409, detail="Cannot delete agent with child agents")

    tx_stmt = select(Transaction).where(Transaction.agent_id == agent_id)
    if (await db.execute(tx_stmt)).first():
        raise HTTPException(status_code=409, detail="Cannot delete agent with existing transactions")

    await db.delete(agent)
    await db.commit()
    await evict_agent(agent_id)


@router.get("/{agent_id}/children", response_model=List[AgentResponse])
async def get_agent_children(
    agent_id: UUID,
    sandbox: bool = Query(False),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = _scope(select(Agent), org_id, sandbox).where(Agent.id == agent_id)
    if not (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    children_stmt = _scope(select(Agent), org_id, sandbox).where(Agent.parent_agent_id == agent_id)
    children_res = await db.execute(children_stmt)
    return children_res.scalars().all()


@router.post("/{agent_id}/kill", response_model=KillSwitchResponse,
             dependencies=[Depends(require_role('admin'))])
async def kill_agent(
    agent_id: UUID,
    mode: str = Query(..., description="'node' | 'subtree' | 'fleet'"),
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delegation-aware kill switch (Phase 10A hardens this with a recursive CTE;
    the Phase-06 implementation here scopes by org AND by the target agent's
    real/sandbox space so a fleet kill never crosses the sandbox boundary).
    """
    start = time.time()
    root_stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    root_agent = (await db.execute(root_stmt)).scalar_one_or_none()
    if not root_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    sandbox = root_agent.is_sandbox

    revoked_ids: list[UUID] = []
    if mode == "node":
        root_agent.status = "revoked"
        revoked_ids.append(root_agent.id)
    elif mode == "fleet":
        fleet_stmt = _scope(select(Agent), org_id, sandbox)
        for a in (await db.execute(fleet_stmt)).scalars().all():
            a.status = "revoked"
            revoked_ids.append(a.id)
    elif mode == "subtree":
        # A recursive CTE keeps deep-tree revocation in the database rather
        # than doing N+1 traversal in application memory.
        descendants = select(Agent.id).where(
            Agent.id == agent_id, Agent.org_id == org_id,
            Agent.is_sandbox == sandbox,
        ).cte(name="descendants", recursive=True)
        descendants = descendants.union_all(
            select(Agent.id).join(descendants, Agent.parent_agent_id == descendants.c.id)
            .where(Agent.org_id == org_id, Agent.is_sandbox == sandbox)
        )
        revoked_ids = list((await db.execute(select(descendants.c.id))).scalars().all())
        await db.execute(
            update(Agent).where(Agent.id.in_(revoked_ids)).values(status="revoked")
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    await write_audit(
        db=db, org_id=org_id, event_type="kill_switch", agent_id=agent_id,
        payload={"mode": mode, "revoked_count": len(revoked_ids),
                 "revoked_ids": [str(r) for r in revoked_ids], "is_sandbox": sandbox},
        actor_user_id=user_id,
        is_sandbox=sandbox,
    )
    await db.commit()

    # Push revoke into Redis so the spend-cap gate short-circuits revoked agents
    # immediately, without waiting for a DB round-trip on the next request.
    for rid in revoked_ids:
        await refresh_status(rid, "revoked")

    return KillSwitchResponse(
        revoked_agent_ids=[str(r) for r in revoked_ids],
        propagation_ms=int((time.time() - start) * 1000),
        mode=mode, timestamp=datetime.now(timezone.utc),
    )


@router.post("/{agent_id}/simulate-exposure", response_model=SimulateExposureResponse,
             dependencies=[Depends(require_role('operator'))])
async def simulate_exposure(
    agent_id: UUID,
    request: SimulateExposureRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Strictly read-only worst-case exposure (Phase 10B adds the read-only test)."""
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    if not (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    total_nodes = 1 + request.max_sub_agents * request.max_delegation_depth
    exposure = float(request.spend_cap) * total_nodes
    return SimulateExposureResponse(
        worst_case_dollar_exposure=exposure,
        breakdown={
            "rootCap": float(request.spend_cap),
            "maxSubAgentsPerLevel": int(request.max_sub_agents),
            "maxDelegationDepth": int(request.max_delegation_depth),
            "totalNodesWorstCase": int(total_nodes),
            "formulaExplained": f"{request.spend_cap} × (1 + {request.max_sub_agents} sub-agents × {request.max_delegation_depth} delegation depth)",
        },
    )
