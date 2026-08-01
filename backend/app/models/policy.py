import uuid
from typing import Any, Dict
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.models.base import Base

class Policy(Base):
    __tablename__ = 'policies'

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    rule_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default=text("100"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="policies")

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, name={self.name}, priority={self.priority}, active={self.active})>"
