from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from .agent import CamelModel

class EscalationResponse(CamelModel):
    id: UUID
    transaction_id: UUID
    agent_name: str  # Joined from transaction -> agent
    amount: float
    merchant_category: str
    risk_score: Optional[float]
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class EscalationAction(BaseModel):
    action: str  # 'approve' | 'deny' | 'adjust_cap'
    adjusted_cap_amount: Optional[float] = None

class EscalationActionResponse(CamelModel):
    id: UUID
    status: str
    reviewed_at: Optional[datetime] = None
