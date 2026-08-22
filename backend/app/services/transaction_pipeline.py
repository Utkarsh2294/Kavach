"""
Phase 06C + 08D + 09A/09B — Transaction pipeline orchestrator.

The full, ordered pipeline for ONE transaction. Each stage is a clean seam so
the layers that joined in Phases 08 and 09 inserted without rewriting what
came before:

    0.  Load agent (verify exists + org-scoped + sandbox-scoped)
    1.  DB-level revoked backstop (authoritative status; survives Redis loss)
    2.  Redis atomic spend-cap gate  (Phase 09A — Lua; revoked/cap -> deny)
    3.  Deterministic rule engine    (Phase 06B)
    4.  ML risk scoring              (Phase 08D — in-process, zero net calls)
    5.  Decision bands              (approve / escalate / deny)
    6.  Persist transaction row
    7.  Persist escalation row on mid-band decisions
    8.  Hash-chained audit log row  (Phase 10D extends write_audit internals)
    9.  Refund Redis spend on deny (only real spend reduces the cap)
    10. WS broadcast                (Phase 09B — Redis pub/sub fanout)

Stages 2 and 4 short-circuit: a revoked / over-cap agent never reaches the rule
engine or the scorer, and a rule-denied transaction is never scored (per the
Phase 08 spec: "after evaluate_rules() passes, call this").
"""
import uuid
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, Policy, Transaction, Escalation
from app.services.rule_engine import evaluate_rules, RuleResult
from app.services.audit import write_audit
from app.config import get_settings
from app.redis_client import RedisClient
from app.services.spend_enforcement import check_and_reserve_spend, release_spend
from app.services.feature_engineering import compute_transaction_features
from app.services.scoring import score_transaction, ModelRegistry, RiskScore
from app.services import feed as feed_service


@dataclass
class TransactionResult:
    transaction: Transaction
    rule_result: RuleResult
    risk_score: Optional[RiskScore] = None
    escalation: Optional[Escalation] = None


def _synthetic_deny_trace(reason: str, detail: dict | None = None) -> RuleResult:
    """A trace entry for denials that happen BEFORE the rule engine (cap/revoked)."""
    entry = {
        "policy_id": None,
        "policy_name": reason,
        "priority": -1,
        "condition": {"op": "system", "value": detail or {}},
        "satisfied": False,
        "system": True,
    }
    return RuleResult(passed=False, denied_by=None, evaluation_trace=[entry])


async def _load_agent_with_depth(db: AsyncSession, org_id, agent_id, is_sandbox: bool) -> Agent:
    """Load the agent (org + sandbox scoped) and resolve its delegation depth."""
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.parent_agent))
        .where(Agent.id == agent_id, Agent.org_id == org_id, Agent.is_sandbox == is_sandbox)
    )
    agent = result.scalar_one_or_none()
    if agent is None:
        raise ValueError(f"Agent {agent_id} not found")

    # Walk the full parent chain to get the true delegation depth.
    current = agent
    depth = 0
    while current.parent_agent_id is not None:
        parent_result = await db.execute(
            select(Agent).where(Agent.id == current.parent_agent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if parent is None:
            break
        current.parent_agent = parent
        current = parent
        depth += 1
    return agent, depth


async def process_transaction(
    db: AsyncSession,
    org_id: uuid.UUID,
    agent_id: uuid.UUID,
    amount: float,
    merchant_category: str,
    actor_user_id: Optional[uuid.UUID] = None,
    is_sandbox: bool = False,
    publish: bool = True,
) -> TransactionResult:
    """
    Run a single transaction through the full governance pipeline.

    `publish=False` is honoured by the sandbox generator + tests so synthetic
    high-frequency traffic doesn't fan out one WS frame per synthetic txn
    unless explicitly desired.
    """
    settings = get_settings()

    # ── 0 + 1. Load agent (org + sandbox scoped) + DB revoked backstop ──
    agent, depth = await _load_agent_with_depth(db, org_id, agent_id, is_sandbox)
    if agent.status == "revoked":
        rule_result = _synthetic_deny_trace("AgentRevoked")
        return await _finalize_deny(
            db=db, settings=settings, org_id=org_id, agent=agent, amount=amount,
            merchant_category=merchant_category, rule_result=rule_result,
            actor_user_id=actor_user_id, is_sandbox=is_sandbox, publish=publish,
            risk_score=None,
        )

    now = datetime.now(timezone.utc)
    tx_context = {
        "amount": float(amount),
        "merchant_category": merchant_category,
        "delegation_depth": depth,
        "agent_type": agent.type,
        "time_of_day_hour": now.hour,
    }

    # ── 2. Redis atomic spend-cap gate (Phase 09A) ──
    spend_reason = "ok"
    spend_allowed = True
    try:
        reserve = await check_and_reserve_spend(
            str(agent.id), float(amount), window=str(settings.spend_window_seconds)
        )
        spend_allowed, spend_reason = reserve.allowed, reserve.reason
    except Exception:
        # Redis unavailable: degrade — DB status already authoritative; skip
        # the cap counter but STILL deny revoked (handled above). Cap
        # enforcement resumes the moment Redis is healthy again.
        spend_reason = "redis_unavailable"

    if not spend_allowed:
        detail = {"reason": spend_reason}
        rule_result = _synthetic_deny_trace(
            "AgentRevoked" if spend_reason == "revoked" else "SpendCapExceeded", detail
        )
        return await _finalize_deny(
            db=db, settings=settings, org_id=org_id, agent=agent, amount=amount,
            merchant_category=merchant_category, rule_result=rule_result,
            actor_user_id=actor_user_id, is_sandbox=is_sandbox, publish=publish,
            risk_score=None,
        )

    # ── 3. Deterministic rule engine (Phase 06B) ──
    policies_result = await db.execute(
        select(Policy).where(Policy.org_id == org_id, Policy.active == True)  # noqa: E712
    )
    policies = list(policies_result.scalars().all())
    rule_result = evaluate_rules(tx_context, policies)

    if not rule_result.passed:
        # Rule-denied: refund the reservation (no real spend) and finalize.
        await release_spend(str(agent.id), float(amount))
        return await _finalize_deny(
            db=db, settings=settings, org_id=org_id, agent=agent, amount=amount,
            merchant_category=merchant_category, rule_result=rule_result,
            actor_user_id=actor_user_id, is_sandbox=is_sandbox, publish=publish,
            risk_score=None,
        )

    # ── 4. ML risk scoring (Phase 08D) ──
    risk_score: Optional[RiskScore] = None
    if ModelRegistry.is_ready():
        feats = await compute_transaction_features(
            db=db, agent=agent, amount=float(amount),
            merchant_category=merchant_category, delegation_depth=depth,
            now=now, max_history=settings.ml_max_history,
        )
        risk_score = score_transaction(str(agent.id), feats)

    # ── 5. Decision bands ──
    if risk_score is not None:
        low, high = settings.ml_threshold_low, settings.ml_threshold_high
        if risk_score.score >= high:
            decision = "deny"
        elif risk_score.score >= low:
            decision = "escalate"
        else:
            decision = "approve"
    else:
        decision = "approve"  # no ML -> rules passed => approve

    # ── 6. Persist the transaction row ──
    tx = Transaction(
        agent_id=agent.id,
        amount=Decimal(str(amount)),
        merchant_category=merchant_category,
        decision=decision,
        risk_score=(risk_score.score if risk_score is not None else None),
        triggered_rule_id=rule_result.denied_by.id if rule_result.denied_by else None,
        delegation_chain_id=uuid.uuid4(),
        is_sandbox=is_sandbox,
    )
    db.add(tx)
    await db.flush()

    # ── 7. Escalation row on mid-band ──
    escalation: Optional[Escalation] = None
    if decision == "escalate":
        escalation = Escalation(
            transaction_id=tx.id, status="pending", is_sandbox=is_sandbox,
        )
        db.add(escalation)
        await db.flush()

    # ── 8. Hash-chained audit log ──
    event_type = {"approve": "grant", "deny": "deny", "escalate": "escalate"}[decision]
    await write_audit(
        db=db, org_id=org_id, event_type=event_type, agent_id=agent.id,
        payload={
            "transaction_id": str(tx.id),
            "amount": float(amount),
            "merchant_category": merchant_category,
            "decision": decision,
            "risk_score": (risk_score.score if risk_score is not None else None),
            "evaluation_trace": rule_result.evaluation_trace,
            "top_features": (
                [{"feature": n, "importance": v} for n, v in risk_score.top_features]
                if risk_score and risk_score.top_features else []
            ),
            "is_sandbox": is_sandbox,
        },
        actor_user_id=actor_user_id,
        is_sandbox=is_sandbox,
    )

    # Deny at the ML band also refunds the spend reservation.
    if decision == "deny":
        await release_spend(str(agent.id), float(amount))

    # ── 10. WS broadcast (Phase 09B — Redis pub/sub fanout) ──
    if publish:
        try:
            await feed_service.publish_feed_event(org_id, is_sandbox,
                feed_service.transaction_update(agent, tx, tx.risk_score))
            spend_now = await RedisClient.get_spend(str(agent.id), "rolling")
            await feed_service.publish_feed_event(org_id, is_sandbox,
                feed_service.agent_status_update(agent, spend_now))
        except Exception:
            pass  # feed must never break the transaction

    return TransactionResult(
        transaction=tx, rule_result=rule_result, risk_score=risk_score,
        escalation=escalation,
    )


async def _finalize_deny(
    *, db, settings, org_id, agent, amount, merchant_category,
    rule_result, actor_user_id, is_sandbox, publish, risk_score,
) -> TransactionResult:
    """Shared finalize path for pre-rule denies (revoked / cap exceeded)."""
    tx = Transaction(
        agent_id=agent.id,
        amount=Decimal(str(amount)),
        merchant_category=merchant_category,
        decision="deny",
        risk_score=None,
        triggered_rule_id=None,
        delegation_chain_id=uuid.uuid4(),
        is_sandbox=is_sandbox,
    )
    db.add(tx)
    await db.flush()

    await write_audit(
        db=db, org_id=org_id, event_type="deny", agent_id=agent.id,
        payload={
            "transaction_id": str(tx.id),
            "amount": float(amount),
            "merchant_category": merchant_category,
            "decision": "deny",
            "evaluation_trace": rule_result.evaluation_trace,
            "is_sandbox": is_sandbox,
        },
        actor_user_id=actor_user_id,
        is_sandbox=is_sandbox,
    )

    if publish:
        try:
            await feed_service.publish_feed_event(org_id, is_sandbox,
                feed_service.transaction_update(agent, tx, None))
        except Exception:
            pass
    return TransactionResult(
        transaction=tx, rule_result=rule_result, risk_score=None, escalation=None,
    )
