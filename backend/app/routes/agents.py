import time
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.deps import get_current_org_id, get_current_user_id
from app.models import Agent, Transaction
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    KillSwitchResponse,
    SimulateExposureRequest,
    SimulateExposureResponse
)
from app.services.audit import write_audit

router = APIRouter(prefix='/api/v1/agents', tags=['Agents'])

@router.get("", response_model=List[AgentResponse])
async def get_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Agent).where(Agent.org_id == org_id)
    if status_filter:
        stmt = stmt.where(Agent.status == status_filter)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    db_agent = Agent(**agent_data.model_dump(), org_id=org_id)
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    return db_agent

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_update: AgentUpdate,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
        
    await db.commit()
    await db.refresh(agent)
    return agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    child_stmt = select(Agent).where(Agent.parent_agent_id == agent_id)
    child_res = await db.execute(child_stmt)
    if child_res.first():
        raise HTTPException(status_code=409, detail="Cannot delete agent with child agents")
        
    tx_stmt = select(Transaction).where(Transaction.agent_id == agent_id)
    tx_res = await db.execute(tx_stmt)
    if tx_res.first():
        raise HTTPException(status_code=409, detail="Cannot delete agent with existing transactions")
        
    await db.delete(agent)
    await db.commit()

@router.get("/{agent_id}/children", response_model=List[AgentResponse])
async def get_agent_children(
    agent_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")
        
    children_stmt = select(Agent).where(Agent.parent_agent_id == agent_id, Agent.org_id == org_id)
    children_res = await db.execute(children_stmt)
    return children_res.scalars().all()

@router.post("/{agent_id}/kill", response_model=KillSwitchResponse)
async def kill_agent(
    agent_id: UUID,
    mode: str = Query(..., description="'node' | 'subtree' | 'fleet'"),
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    result = await db.execute(stmt)
    root_agent = result.scalar_one_or_none()
    if not root_agent and mode != 'fleet':
        raise HTTPException(status_code=404, detail="Agent not found")

    revoked_ids = []
    
    if mode == 'node':
        root_agent.status = 'revoked'
        revoked_ids.append(root_agent.id)
        
    elif mode == 'fleet':
        fleet_stmt = select(Agent).where(Agent.org_id == org_id)
        fleet_res = await db.execute(fleet_stmt)
        agents = fleet_res.scalars().all()
        for a in agents:
            a.status = 'revoked'
            revoked_ids.append(a.id)
            
    elif mode == 'subtree':
        fleet_stmt = select(Agent).where(Agent.org_id == org_id)
        fleet_res = await db.execute(fleet_stmt)
        all_agents = fleet_res.scalars().all()
        
        children_map = {}
        for a in all_agents:
            children_map.setdefault(a.parent_agent_id, []).append(a)
            
        def collect_descendants(curr_id):
            res = [curr_id]
            for child in children_map.get(curr_id, []):
                res.extend(collect_descendants(child.id))
            return res
            
        descendant_ids = collect_descendants(agent_id)
        for a in all_agents:
            if a.id in descendant_ids:
                a.status = 'revoked'
                revoked_ids.append(a.id)
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")
        
    # Write audit BEFORE commit so it's in the same transaction
    await write_audit(
        db=db,
        org_id=org_id,
        event_type="kill_switch",
        agent_id=agent_id,
        payload={"mode": mode, "revoked_count": len(revoked_ids), "revoked_ids": [str(rid) for rid in revoked_ids]},
        actor_user_id=user_id
    )
    
    await db.commit()
    propagation_ms = int((time.time() - start_time) * 1000)
    
    return KillSwitchResponse(
        revoked_agent_ids=[str(rid) for rid in revoked_ids],
        propagation_ms=propagation_ms,
        mode=mode,
        timestamp=datetime.now(timezone.utc),
    )

@router.post("/{agent_id}/simulate-exposure", response_model=SimulateExposureResponse)
async def simulate_exposure(
    agent_id: UUID,
    request: SimulateExposureRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")
        
    total_nodes = 1 + request.max_sub_agents * request.max_delegation_depth
    exposure = request.spend_cap * total_nodes
    
    return SimulateExposureResponse(
        worst_case_dollar_exposure=exposure,
        breakdown={
            "rootCap": request.spend_cap,
            "maxSubAgentsPerLevel": request.max_sub_agents,
            "maxDelegationDepth": request.max_delegation_depth,
            "totalNodesWorstCase": total_nodes,
            "formulaExplained": f"{request.spend_cap} × (1 + {request.max_sub_agents} sub-agents × {request.max_delegation_depth} delegation depth)",
        },
    )
