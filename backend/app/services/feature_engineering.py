"""
Phase 08D — Online feature engineering for the ML risk scorer.

Builds the per-agent rolling behavioral feature vector from the agent's
recent in-DB transactions + the current transaction, so the served
`score_transaction()` operates on the same feature contract the models
were trained on (`ml/features.py::ML_FEATURES`).

The math here MUST stay byte-for-byte identical to `ml/features.build_features()`.
`backend/tests/test_feature_engineering.py` asserts that equivalence against the
importable `ml.features` module, so any drift fails CI.
"""

import math
import uuid
from datetime import datetime, timezone, timedelta
from datetime import timezone as _tz
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, Agent

# Must match ml/features.py::ML_FEATURES exactly. Kept here as a frozen copy so
# the backend has zero filesystem/path dependency on the ml/ package at serve time.
ML_FEATURES = [
    "amount",
    "amount_deviation",
    "amount_to_cap_ratio",
    "velocity_1h",
    "merchant_entropy",
    "time_of_day_hour",
    "time_of_day_zscore",
    "delegation_depth",
]


def shannon_entropy(category_counts: dict) -> float:
    total = sum(category_counts.values())
    if total <= 0:
        return 0.0
    ent = 0.0
    for c in category_counts.values():
        if c > 0:
            p = c / total
            ent -= p * math.log(p)
    return ent


def build_features(
    *,
    amount: float,
    agent_mean_amount: float,
    agent_cap: float,
    velocity_1h: float,
    merchant_entropy: float,
    time_of_day_hour: int,
    agent_mean_hour: float,
    agent_std_hour: float,
    delegation_depth: int,
) -> dict:
    """Identical math to ml/features.build_features — drift asserted by tests."""
    mean_amount = float(agent_mean_amount) if agent_mean_amount and agent_mean_amount > 0 else 1.0
    cap = float(agent_cap) if agent_cap and agent_cap > 0 else 1.0
    hour = float(time_of_day_hour)
    mean_hour = float(agent_mean_hour)
    std_hour = float(agent_std_hour) if agent_std_hour and agent_std_hour > 0 else 1.0

    amount_dev = (float(amount) - agent_mean_amount) / (mean_amount + 1e-9)
    amount_dev = max(min(amount_dev, 50.0), -50.0)

    hour_z = (hour - mean_hour) / (std_hour + 1e-9)
    hour_z = max(min(hour_z, 6.0), -6.0)

    return {
        "amount": float(amount),
        "amount_deviation": float(amount_dev),
        "amount_to_cap_ratio": float(amount) / cap,
        "velocity_1h": float(velocity_1h),
        "merchant_entropy": float(merchant_entropy),
        "time_of_day_hour": hour,
        "time_of_day_zscore": float(hour_z),
        "delegation_depth": float(delegation_depth),
    }


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_tz.utc)
    return dt.astimezone(_tz.utc)


async def compute_transaction_features(
    db: AsyncSession,
    agent: Agent,
    amount: float,
    merchant_category: str,
    delegation_depth: int,
    now: Optional[datetime] = None,
    max_history: int = 50,
) -> dict:
    """
    Compute the canonical behavioral feature dict for a *proposed* transaction
    by agent `agent`, using the agent's prior Transaction rows for rolling stats.

    Returns a dict containing every key in ML_FEATURES plus `agent_type` (needed
    by the XGBoost one-hot layer and to select the per-type IsolationForest).
    """
    now = now or datetime.now(timezone.utc)
    history_cutoff = now - timedelta(hours=1)

    stmt = (
        select(Transaction)
        .where(Transaction.agent_id == agent.id)
        .order_by(Transaction.timestamp.desc())
        .limit(max_history)
    )
    res = await db.execute(stmt)
    txns = res.scalars().all()

    cap = float(agent.spend_cap_current or 0.0)

    # Rolling amount mean over prior history.
    if txns:
        amounts = [float(t.amount) for t in txns]
        agent_mean_amount = sum(amounts) / len(amounts)
    else:
        agent_mean_amount = float(amount)

    # Velocity: count of prior txns within the rolling 1h window.
    velocity_1h = sum(1 for t in txns if _to_utc(t.timestamp) >= history_cutoff)

    # Merchant-category entropy over the prior distribution.
    cat_counts: dict = {}
    for t in txns:
        cat_counts[t.merchant_category] = cat_counts.get(t.merchant_category, 0) + 1
    merchant_entropy = shannon_entropy(cat_counts)

    # Per-agent hour-of-day pattern.
    if txns:
        hours = [_to_utc(t.timestamp).hour for t in txns]
        agent_mean_hour = sum(hours) / len(hours)
        if len(hours) > 1:
            var = sum((h - agent_mean_hour) ** 2 for h in hours) / (len(hours) - 1)
            agent_std_hour = math.sqrt(var)
        else:
            agent_std_hour = 1.0
    else:
        agent_mean_hour = 12.0
        agent_std_hour = 1.0

    feats = build_features(
        amount=float(amount),
        agent_mean_amount=agent_mean_amount,
        agent_cap=cap,
        velocity_1h=float(velocity_1h),
        merchant_entropy=merchant_entropy,
        time_of_day_hour=now.hour,
        agent_mean_hour=agent_mean_hour,
        agent_std_hour=agent_std_hour,
        delegation_depth=int(delegation_depth),
    )
    # Non-feature metadata the scorer needs to route to the right per-type model.
    feats["agent_type"] = str(agent.type)
    feats["agent_id"] = str(agent.id)
    return feats


def feature_vector(features: dict, names: list[str] | None = None) -> list[float]:
    names = names if names is not None else ML_FEATURES
    return [float(features.get(n, 0.0)) for n in names]
