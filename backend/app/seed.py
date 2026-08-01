"""
Kavach Backend — Database seed script.

Creates realistic test data for local development:
  - 1 organization (Meridian Financial Corp)
  - 2 users (admin + operator)
  - 8 agents with a 3-level delegation chain
  - 8 policies with varying priorities

Run: python -m app.seed   (from the backend/ directory)

Uses fixed UUID5 seeds so the script is idempotent — running it twice
doesn't crash or create duplicates.
"""

import uuid
import sys
import os
from decimal import Decimal

# Ensure 'app' is importable when run as `python -m app.seed`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    Base,
    Organization,
    User,
    Agent,
    Policy,
)

# ── Fixed UUID namespace for deterministic seed IDs ──────────────────────────
NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def make_id(name: str) -> uuid.UUID:
    """Deterministic UUID from a human-readable name."""
    return uuid.uuid5(NS, name)


# ── Pre-computed IDs ─────────────────────────────────────────────────────────
ORG_ID = make_id("meridian-financial")
ADMIN_ID = make_id("admin-user")
OPERATOR_ID = make_id("operator-user")

AGENT_TREASURY = make_id("agent-treasury")
AGENT_TRAVEL = make_id("agent-travel")
AGENT_SUBSCRIPTION = make_id("agent-subscription")
AGENT_PROCUREMENT = make_id("agent-procurement")
AGENT_HOTEL = make_id("agent-hotel")
AGENT_FLIGHT = make_id("agent-flight")
AGENT_OFFICE = make_id("agent-office")
AGENT_IT = make_id("agent-it")

POLICY_IDS = [make_id(f"policy-{i}") for i in range(1, 9)]


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt via passlib."""
    try:
        from passlib.hash import bcrypt
        return bcrypt.using(rounds=12).hash(plain)
    except ImportError:
        # Fallback: store a clearly-marked placeholder if passlib isn't installed
        return f"$PLACEHOLDER${plain}"


def seed():
    """Populate the database with test data."""
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, echo=False)

    # Verify tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "organizations" not in tables:
        print("ERROR: Tables not found. Run 'alembic upgrade head' first.")
        sys.exit(1)

    password_hash = hash_password("password123")

    with Session(engine) as session:
        # ── Check if already seeded ──────────────────────────────────────
        existing = session.get(Organization, ORG_ID)
        if existing:
            print("✓ Database already seeded (Meridian Financial Corp exists). Skipping.")
            return

        # ── 1. Organization ──────────────────────────────────────────────
        org = Organization(id=ORG_ID, name="Meridian Financial Corp")
        session.add(org)
        session.flush()
        print("  Created organization: Meridian Financial Corp")

        # ── 2. Users ─────────────────────────────────────────────────────
        admin = User(
            id=ADMIN_ID,
            org_id=ORG_ID,
            name="Admin User",
            email="admin@kavach.dev",
            password_hash=password_hash,
            role="admin",
        )
        operator = User(
            id=OPERATOR_ID,
            org_id=ORG_ID,
            name="Test User",
            email="test@kavach.dev",
            password_hash=password_hash,
            role="operator",
        )
        session.add_all([admin, operator])
        session.flush()
        print("  Created users: admin@kavach.dev, test@kavach.dev")

        # ── 3. Agents — 3-level delegation chain ─────────────────────────
        #
        #   Level 0:  Treasury Operations
        #               ├── Travel Booking Agent        (Level 1)
        #               │     ├── Hotel Reservations    (Level 2)
        #               │     └── Flight Booking        (Level 2)
        #               ├── Subscription Manager        (Level 1)
        #               └── Procurement Bot             (Level 1)
        #                     ├── Office Supplies        (Level 2)
        #                     └── IT Equipment           (Level 2)

        agents = [
            # Level 0 — root
            Agent(
                id=AGENT_TREASURY,
                org_id=ORG_ID,
                name="Treasury Operations",
                type="procurement",
                parent_agent_id=None,
                trust_score=0.92,
                spend_cap_current=Decimal("100000.00"),
                status="active",
            ),
            # Level 1
            Agent(
                id=AGENT_TRAVEL,
                org_id=ORG_ID,
                name="Travel Booking Agent",
                type="travel",
                parent_agent_id=AGENT_TREASURY,
                trust_score=0.85,
                spend_cap_current=Decimal("25000.00"),
                status="active",
            ),
            Agent(
                id=AGENT_SUBSCRIPTION,
                org_id=ORG_ID,
                name="Subscription Manager",
                type="subscription",
                parent_agent_id=AGENT_TREASURY,
                trust_score=0.78,
                spend_cap_current=Decimal("15000.00"),
                status="active",
            ),
            Agent(
                id=AGENT_PROCUREMENT,
                org_id=ORG_ID,
                name="Procurement Bot",
                type="procurement",
                parent_agent_id=AGENT_TREASURY,
                trust_score=0.88,
                spend_cap_current=Decimal("50000.00"),
                status="active",
            ),
            # Level 2 — children of Travel
            Agent(
                id=AGENT_HOTEL,
                org_id=ORG_ID,
                name="Hotel Reservations",
                type="sub-agent",
                parent_agent_id=AGENT_TRAVEL,
                trust_score=0.72,
                spend_cap_current=Decimal("10000.00"),
                status="active",
            ),
            Agent(
                id=AGENT_FLIGHT,
                org_id=ORG_ID,
                name="Flight Booking",
                type="sub-agent",
                parent_agent_id=AGENT_TRAVEL,
                trust_score=0.80,
                spend_cap_current=Decimal("15000.00"),
                status="active",
            ),
            # Level 2 — children of Procurement
            Agent(
                id=AGENT_OFFICE,
                org_id=ORG_ID,
                name="Office Supplies",
                type="sub-agent",
                parent_agent_id=AGENT_PROCUREMENT,
                trust_score=0.65,
                spend_cap_current=Decimal("5000.00"),
                status="active",
            ),
            Agent(
                id=AGENT_IT,
                org_id=ORG_ID,
                name="IT Equipment",
                type="sub-agent",
                parent_agent_id=AGENT_PROCUREMENT,
                trust_score=0.70,
                spend_cap_current=Decimal("20000.00"),
                status="active",
            ),
        ]
        session.add_all(agents)
        session.flush()
        print(f"  Created {len(agents)} agents with 3-level delegation chain")

        # ── 4. Policies ──────────────────────────────────────────────────
        policies = [
            Policy(
                id=POLICY_IDS[0],
                org_id=ORG_ID,
                name="Max Single Transaction",
                rule_json={"field": "amount", "op": "<=", "value": 10000},
                priority=10,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[1],
                org_id=ORG_ID,
                name="Block Gaming",
                rule_json={
                    "field": "merchant_category",
                    "op": "not_in",
                    "value": ["gambling", "gaming", "casino"],
                },
                priority=20,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[2],
                org_id=ORG_ID,
                name="Delegation Depth Limit",
                rule_json={"field": "delegation_depth", "op": "<=", "value": 3},
                priority=30,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[3],
                org_id=ORG_ID,
                name="Business Hours Only",
                rule_json={
                    "all": [
                        {"field": "time_of_day_hour", "op": ">=", "value": 8},
                        {"field": "time_of_day_hour", "op": "<=", "value": 18},
                    ]
                },
                priority=40,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[4],
                org_id=ORG_ID,
                name="Sub-Agent Spend Cap",
                rule_json={
                    "all": [
                        {"field": "agent_type", "op": "==", "value": "sub-agent"},
                        {"field": "amount", "op": "<=", "value": 5000},
                    ]
                },
                priority=50,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[5],
                org_id=ORG_ID,
                name="Travel Category Limit",
                rule_json={
                    "all": [
                        {
                            "field": "merchant_category",
                            "op": "in",
                            "value": ["airline", "hotel", "car_rental"],
                        },
                        {"field": "amount", "op": "<=", "value": 3000},
                    ]
                },
                priority=60,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[6],
                org_id=ORG_ID,
                name="High-Value Review",
                rule_json={"field": "amount", "op": ">=", "value": 7500},
                priority=70,
                active=True,
            ),
            Policy(
                id=POLICY_IDS[7],
                org_id=ORG_ID,
                name="Procurement Approval",
                rule_json={
                    "all": [
                        {"field": "agent_type", "op": "==", "value": "procurement"},
                        {"field": "amount", "op": ">=", "value": 25000},
                    ]
                },
                priority=80,
                active=True,
            ),
        ]
        session.add_all(policies)
        session.flush()
        print(f"  Created {len(policies)} policies")

        # ── Commit ───────────────────────────────────────────────────────
        session.commit()
        print("\n✓ Seed complete!")
        print(f"  Organization: {org.name} ({org.id})")
        print(f"  Users: admin@kavach.dev (admin), test@kavach.dev (operator)")
        print(f"  Password: password123")
        print(f"  Agents: {len(agents)} (3-level tree)")
        print(f"  Policies: {len(policies)}")


if __name__ == "__main__":
    seed()
