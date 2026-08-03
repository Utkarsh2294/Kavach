from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from .agent import CamelModel

class AuditLogResponse(CamelModel):
    id: UUID
    org_id: UUID
    event_type: str
    agent_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    payload: dict
    prev_hash: Optional[str] = None
    this_hash: Optional[str] = None
    timestamp: datetime

class AuditVerifyResponse(CamelModel):
    valid: bool
    records_verified: int
    breaks: list[dict]

class NistMappingResponse(BaseModel):
    mappings: list[dict]
