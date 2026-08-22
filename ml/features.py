"""
Canonical ML feature contract for the Kavach risk-scoring layer.

This module is the SINGLE source of truth for the feature names and the
feature-building formulas used by BOTH the offline training pipeline
(`train_isolation_forest.py`, `train_xgboost.py`) and the online serving
layer (`backend/app/services/scoring.py`).

Design rules (from Phase 08 spec):
  * No raw balance columns are fed to any model — only deltas/ratios
    engineered in `augment.py`. The serving-equivalent features below are
    all derivable from the transaction stream + the agent record, because
    bank balance columns are NOT available on the Kavach hot path.
  * The served feature vector must be computable at inference time with
    zero network calls — only from the agent's recent transactions in the
    DB and the agent row itself.
  * Names and order are frozen: artifacts store `feature_names` and the
    serving layer must produce exactly these keys.

If you change anything here you must retrain BOTH models and re-verify
`ml/validation_report.md`.
"""

import math

# Ordered, frozen list of features consumed by the served models.
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

# Feature importances are reported for these in the rolling-behavioral group.
BEHAVIORAL_FEATURES = [
    "amount_deviation",
    "amount_to_cap_ratio",
    "velocity_1h",
    "merchant_entropy",
    "time_of_day_zscore",
]


def shannon_entropy(category_counts: dict) -> float:
    """Shannon entropy (base e) over a category->count distribution."""
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
    """
    Build the canonical feature dictionary from raw inputs.

    This pure function is shared by training and serving so the math is
    provably identical. All values are floats; callers vectorize per the
    `ML_FEATURES` order.
    """
    mean_amount = float(agent_mean_amount) if agent_mean_amount and agent_mean_amount > 0 else 1.0
    cap = float(agent_cap) if agent_cap and agent_cap > 0 else 1.0
    hour = float(time_of_day_hour)
    mean_hour = float(agent_mean_hour)
    std_hour = float(agent_std_hour) if agent_std_hour and agent_std_hour > 0 else 1.0

    amount_dev = (float(amount) - agent_mean_amount) / (mean_amount + 1e-9)
    # Clamp to a sane range to avoid runaway outliers dominating the model.
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


def feature_vector(features: dict, names: list[str] | None = None) -> list[float]:
    """Order a feature dict into a vector matching `names` (default ML_FEATURES)."""
    names = names if names is not None else ML_FEATURES
    return [float(features.get(n, 0.0)) for n in names]
