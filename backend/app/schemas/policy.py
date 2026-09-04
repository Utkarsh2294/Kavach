from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from .agent import CamelModel

class PolicyCreate(CamelModel):
    name: str
    rule_json: dict  # The policy condition JSON
    priority: int = 100
    active: bool = True

class PolicyUpdate(CamelModel):
    name: Optional[str] = None
    rule_json: Optional[dict] = None
    priority: Optional[int] = None
    active: Optional[bool] = None

class PolicyResponse(CamelModel):
    id: UUID
    org_id: UUID
    name: str
    rule_json: dict
    priority: int
    active: bool
    created_at: datetime

class DryRunRequest(BaseModel):
    conditions: list[dict]  # [{"field": "amount", "op": "<=", "value": 250}]

class DryRunDiffItem(CamelModel):
    tx_id: str
    agent_name: str
    amount: float
    merchant_category: str
    risk_score: Optional[float]
    before: str
    after: str
    triggered: bool

class DryRunResponse(CamelModel):
    before_after_diff: list[DryRunDiffItem]
    summary: dict
