"""Sandbox isolation columns (Phase 09C) — is_sandbox on the four data tables.

Adds a NOT NULL boolean `is_sandbox` (default false) to agents, transactions,
audit_log, and escalation_queue, plus an index on agents.is_sandbox to keep
the "scope sandbox rows out of every real fleet query" filter cheap.

Revision ID: 002
Revises: 001
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("agents", "transactions", "audit_log", "escalation_queue"):
        op.add_column(
            table,
            sa.Column(
                "is_sandbox",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )
    op.create_index("idx_agents_is_sandbox", "agents", ["is_sandbox"])


def downgrade() -> None:
    op.drop_index("idx_agents_is_sandbox", table_name="agents")
    for table in ("escalation_queue", "audit_log", "transactions", "agents"):
        op.drop_column(table, "is_sandbox")
