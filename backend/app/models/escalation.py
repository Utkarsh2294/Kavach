import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import Text, DateTime, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base

class Escalation(Base):
    __tablename__ = 'escalation_queue'

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transactions.id"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text, 
        nullable=False, 
        default='pending',
        server_default=text("'pending'")
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    transaction: Mapped["Transaction"] = relationship("Transaction")
    reviewer: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<Escalation(id={self.id}, transaction_id={self.transaction_id}, status={self.status})>"
