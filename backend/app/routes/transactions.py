from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.deps import get_current_org_id, get_current_user_id, require_role
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.models import Transaction, Agent
from app.services.transaction_pipeline import process_transaction

router = APIRouter(prefix='/api/v1/transactions', tags=['Transactions'])


@router.post("", response_model=TransactionResponse,
             dependencies=[Depends(require_role('operator'))])
async def create_transaction(
    tx_data: TransactionCreate,
    sandbox: bool = Query(False, description="Ingest into the sandbox fleet"),
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await process_transaction(
            db=db, org_id=org_id, agent_id=tx_data.agent_id, amount=tx_data.amount,
            merchant_category=tx_data.merchant_category, actor_user_id=user_id,
            is_sandbox=sandbox,
        )
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    tx = result.transaction
    return TransactionResponse(
        id=tx.id, agent_id=tx.agent_id, amount=float(tx.amount),
        merchant_category=tx.merchant_category, timestamp=tx.timestamp,
        decision=tx.decision, risk_score=tx.risk_score,
        triggered_rule_id=tx.triggered_rule_id, delegation_chain_id=tx.delegation_chain_id,
        evaluation_trace=result.rule_result.evaluation_trace,
    )


@router.get("", response_model=List[TransactionResponse])
async def get_transactions(
    agent_id: Optional[UUID] = Query(None),
    sandbox: bool = Query(False, description="Show sandbox transactions"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Transaction)
        .join(Agent, Transaction.agent_id == Agent.id)
        .where(Agent.org_id == org_id, Agent.is_sandbox == sandbox)
        .order_by(Transaction.timestamp.desc())
    )
    if agent_id:
        stmt = stmt.where(Transaction.agent_id == agent_id)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()
