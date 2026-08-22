import uuid
from typing import Optional, Any, Dict
from datetime import datetime
from sqlalchemy import Text, DateTime, Boolean, text, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.models.base import Base

class AuditLog(Base):
    __tablename__ = 'audit_log'

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    prev_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    this_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Phase 09C sandbox isolation.
    is_sandbox: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization")
    agent: Mapped[Optional["Agent"]] = relationship("Agent")
    actor_user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type})>"
