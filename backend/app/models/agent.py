import uuid
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Float, Numeric, DateTime, text, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base

class Agent(Base):
    __tablename__ = 'agents'

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
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    parent_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True,
        index=True
    )
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5, server_default=text("0.5"))
    spend_cap_current: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='active', server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="agents")
    parent_agent: Mapped[Optional["Agent"]] = relationship("Agent", remote_side=[id], back_populates="child_agents")
    child_agents: Mapped[List["Agent"]] = relationship("Agent", back_populates="parent_agent")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"
