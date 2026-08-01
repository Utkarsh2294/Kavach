import uuid
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Text, Float, Numeric, DateTime, text, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base

class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    merchant_category: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    triggered_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("policies.id"),
        nullable=True
    )
    delegation_chain_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    agent: Mapped["Agent"] = relationship("Agent")
    triggered_rule: Mapped[Optional["Policy"]] = relationship("Policy")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, amount={self.amount}, decision={self.decision})>"
