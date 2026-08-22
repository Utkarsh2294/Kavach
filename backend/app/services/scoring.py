"""
Phase 08D — Model serving integration.

Loads BOTH ML artifacts (Isolation Forest + XGBoost) once at FastAPI startup
into a process-level registry and scores transactions in-process with ZERO
inference-time network calls (the permanent Phase 08 architectural constraint).

Signature (Phase 08 interface contract):
    score_transaction(agent_id: str, transaction_features: dict) -> RiskScore

RiskScore fields:
    score              : float 0..1   (served risk band decision source)
    isolation_forest_flag : bool    (per-agent-type unsupervised anomaly flag)
    xgboost_score      : float 0..1   (calibrated probability of is_agent_anomaly)
    top_features       : list[(name, importance)]   (explainability for the UI audit log)
"""

import pickle
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import get_settings
from app.services.feature_engineering import ML_FEATURES, build_features  # noqa: F401


@dataclass
class RiskScore:
    score: float
    isolation_forest_flag: bool
    xgboost_score: float
    top_features: list


# ── Process-level singleton ──────────────────────────────────────────────────


class ModelRegistry:
    """Holds both loaded artifacts. Initialized once at app startup."""

    _iforest: Optional[dict] = None
    _xgb: Optional[dict] = None
    _lock = threading.Lock()
    _loaded = False

    @classmethod
    def load(cls) -> None:
        """Load both artifacts from disk into the registry (idempotent)."""
        settings = get_settings()
        art_dir = Path(settings.resolved_ml_artifacts_dir)
        cls._lock.acquire()
        try:
            if cls._loaded:
                return
            if not settings.ml_enabled:
                cls._loaded = True
                return
            if_path = art_dir / "isolation_forest.pkl"
            xgb_path = art_dir / "xgboost_risk.pkl"
            if not if_path.exists() or not xgb_path.exists():
                # Artifacts missing -> degrade gracefully (rules still enforce).
                cls._loaded = True
                return
            with if_path.open("rb") as f:
                cls._iforest = pickle.load(f)
            with xgb_path.open("rb") as f:
                cls._xgb = pickle.load(f)
            cls._loaded = True
        finally:
            cls._lock.release()

    @classmethod
    def is_ready(cls) -> bool:
        return cls._loaded and cls._iforest is not None and cls._xgb is not None

    @classmethod
    def iforest(cls) -> Optional[dict]:
        return cls._iforest

    @classmethod
    def xgb(cls) -> Optional[dict]:
        return cls._xgb

    @classmethod
    def reset(cls) -> None:
        """Test helper — forces a fresh reload."""
        cls._iforest = None
        cls._xgb = None
        cls._loaded = False


# ── Scoring ─────────────────────────────────────────────────────────────────


def _isolation_flag_and_score(features: dict, agent_type: str) -> tuple[bool, float]:
    art = ModelRegistry.iforest()
    if not art:
        return (False, 0.0)
    sub = (art.get("models") or {}).get(agent_type) or art.get("default")
    if not sub:
        return (False, 0.0)
    names = sub["feature_names"]
    X = np.array([[float(features.get(n, 0.0)) for n in names]], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    Xs = sub["scaler"].transform(X)
    pred = int(sub["model"].predict(Xs)[0])
    # decision_function: higher = more normal; negative = more anomalous.
    df = float(sub["model"].decision_function(Xs)[0])
    iso_norm = max(0.0, min(1.0, 0.5 - df))  # ~0 normal, ~1 anomaly
    is_flag = pred == -1
    return (is_flag, iso_norm)


def _xgboost_score(features: dict, agent_type: str) -> float:
    art = ModelRegistry.xgb()
    if not art:
        return 0.0
    agent_types = art.get("agent_types", [])
    feat = [float(features.get(n, 0.0)) for n in art["feature_names"]]
    onehot = [0.0] * len(agent_types)
    if agent_type in agent_types:
        onehot[agent_types.index(agent_type)] = 1.0
    X = np.array([feat + onehot], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    proba = float(art["model"].predict_proba(X)[0, 1])
    return max(0.0, min(1.0, proba))


def score_transaction(agent_id: str, transaction_features: dict) -> RiskScore:
    """Score one transaction. Loads NO artifacts here — registry is prewarm.

    Falls back to a zero-risk score if the registry is missing (e.g. artifacts
    not built yet or ml_enabled=False); the deterministic rule engine still
    enforces policy in that case, so governance never silently degrades.
    """
    agent_type = str(transaction_features.get("agent_type", ""))
    iso_flag, iso_score = _isolation_flag_and_score(transaction_features, agent_type)
    xgb = _xgboost_score(transaction_features, agent_type)

    # Combined 0..1 risk score: the XGBoost calibrated probability dominates, but
    # an Isolation Forest flag (catches unknown-unknowns XGBoost may miss) can
    # raise the score into at least the escalate band so it never gets silently
    # approved only because XGB under-scored a genuinely anomalous pattern.
    isolation_contribution = iso_score if iso_flag else iso_score * 0.5
    score = max(xgb, isolation_contribution)
    if iso_flag and xgb < 0.30:
        # Isolation forest is confident this is anomalous even though XGB is low;
        # bump the served score so it reaches human review rather than silent approve.
        score = max(score, 0.30)

    top_features = []
    xgb_art = ModelRegistry.xgb()
    if xgb_art:
        top_features = list(xgb_art.get("feature_importances", [])[:6])

    return RiskScore(
        score=float(max(0.0, min(1.0, score))),
        isolation_forest_flag=bool(iso_flag),
        xgboost_score=float(max(0.0, min(1.0, xgb))),
        top_features=top_features,
    )


def score_to_credit_0_100(score: float) -> int:
    """Convert the 0..1 served score into the 0..100 integer the WS feed emits."""
    return int(round(min(1.0, max(0.0, float(score))) * 100))
