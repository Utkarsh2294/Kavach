from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional
from uuid import UUID
from datetime import datetime

class CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

class AgentCreate(BaseModel):
    name: str
    type: str  # 'travel' | 'subscription' | 'procurement' | 'sub-agent'
    parent_agent_id: Optional[UUID] = None
    trust_score: float = 0.5
    spend_cap_current: float  # Decimal in DB but float in API
    status: str = 'active'

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    parent_agent_id: Optional[UUID] = None
    trust_score: Optional[float] = None
    spend_cap_current: Optional[float] = None
    status: Optional[str] = None

class AgentResponse(CamelModel):
    id: UUID
    org_id: UUID
    name: str
    type: str
    parent_agent_id: Optional[UUID] = None
    trust_score: float
    spend_cap_current: float
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)

class KillSwitchRequest(BaseModel):
    # mode comes from query param, not body
    pass

class KillSwitchResponse(CamelModel):
    revoked_agent_ids: list[str]
    propagation_ms: int
    mode: str
    timestamp: datetime

class SimulateExposureRequest(CamelModel):
    spend_cap: float
    max_sub_agents: int
    max_delegation_depth: int

class SimulateExposureResponse(CamelModel):
    worst_case_dollar_exposure: float
    breakdown: dict
