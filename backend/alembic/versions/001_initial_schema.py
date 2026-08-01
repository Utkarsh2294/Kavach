"""Initial schema — all 7 tables and 5 indexes from Phase 05 spec.

Revision ID: 001
Revises: None
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. organizations ─────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organizations"),
    )

    # ── 2. users (FK → organizations) ────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "org_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "name", sa.Text(), server_default=sa.text("''"), nullable=False
        ),
        sa.Column(
            "role",
            sa.Text(),
            server_default=sa.text("'operator'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name="fk_users_org_id_organizations",
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # ── 3. agents (FK → organizations, self-referential) ─────────────────
    op.create_table(
        "agents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "org_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column(
            "parent_agent_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "trust_score",
            sa.Float(),
            server_default=sa.text("0.5"),
            nullable=False,
        ),
        sa.Column("spend_cap_current", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agents"),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name="fk_agents_org_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["parent_agent_id"],
            ["agents.id"],
            name="fk_agents_parent_agent_id_agents",
        ),
    )
    op.create_index("idx_agents_parent", "agents", ["parent_agent_id"])
    op.create_index("idx_agents_org", "agents", ["org_id"])

    # ── 4. policies (FK → organizations) ─────────────────────────────────
    op.create_table(
        "policies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "org_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("rule_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default=sa.text("100"),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_policies"),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name="fk_policies_org_id_organizations",
        ),
    )

    # ── 5. transactions (FK → agents, FK → policies) ─────────────────────
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "agent_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("merchant_category", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column(
            "triggered_rule_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "delegation_chain_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_transactions"),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_transactions_agent_id_agents",
        ),
        sa.ForeignKeyConstraint(
            ["triggered_rule_id"],
            ["policies.id"],
            name="fk_transactions_triggered_rule_id_policies",
        ),
    )
    op.create_index(
        "idx_transactions_agent", "transactions", ["agent_id"]
    )
    op.create_index(
        "idx_transactions_delegation_chain",
        "transactions",
        ["delegation_chain_id"],
    )

    # ── 6. audit_log (FK → organizations, agents, users) ─────────────────
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "org_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "agent_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("prev_hash", sa.Text(), nullable=True),
        sa.Column("this_hash", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name="fk_audit_log_org_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_audit_log_agent_id_agents",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_audit_log_actor_user_id_users",
        ),
    )
    op.create_index("idx_audit_log_org", "audit_log", ["org_id"])

    # ── 7. escalation_queue (FK → transactions, users) ───────────────────
    op.create_table(
        "escalation_queue",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.PrimaryKeyConstraint("id", name="pk_escalation_queue"),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_escalation_queue_transaction_id_transactions",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            name="fk_escalation_queue_reviewer_id_users",
        ),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("escalation_queue")
    op.drop_index("idx_audit_log_org", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index(
        "idx_transactions_delegation_chain", table_name="transactions"
    )
    op.drop_index("idx_transactions_agent", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("policies")
    op.drop_index("idx_agents_org", table_name="agents")
    op.drop_index("idx_agents_parent", table_name="agents")
    op.drop_table("agents")
    op.drop_table("users")
    op.drop_table("organizations")
