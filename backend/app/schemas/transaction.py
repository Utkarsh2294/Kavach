from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from .agent import CamelModel

class TransactionCreate(BaseModel):
    agent_id: UUID
    amount: float
    merchant_category: str

class TransactionResponse(CamelModel):
    id: UUID
    agent_id: UUID
    amount: float
    merchant_category: str
    timestamp: datetime
    decision: str  # 'approve' | 'deny' | 'escalate'
    risk_score: Optional[float] = None
    triggered_rule_id: Optional[UUID] = None
    delegation_chain_id: UUID
    evaluation_trace: Optional[list[dict]] = None  # Included in POST response
