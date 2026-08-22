"""
Phase 08B — Isolation Forest (unsupervised) anomaly detector.

Trained PER-AGENT-TYPE on the rolling behavioral features only, so the model
flags transactions that are "unusual for an agent of THIS type" rather than
applying one global threshold to everyone.

Saves a single pickled artifact dict keyed by agent_type to:
    ml/artifacts/isolation_forest.pkl

Artifact schema (served by `backend/app/services/scoring.py`):
    {
      "models": {
         "travel":       {"model": IsolationForest, "feature_names": [...], "scaler": StandardScaler},
         "subscription": {...},
         ...
      },
      "default": {"model":..., "feature_names":..., "scaler":...},   # fallback, 'orchestrator'-trained
      "feature_names": ML_FEATURES,
      "agent_types": [...],
      "version": "1.0",
    }

Zero inference-time network calls: the artifact is loaded once at FastAPI
startup and `score` runs in-process.

Run: cd ml && python train_isolation_forest.py
"""

import sys
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from features import ML_FEATURES

DATA_PATH = Path(__file__).resolve().parent / "data" / "augmented.csv"
ART_DIR = Path(__file__).resolve().parent / "artifacts"
OUT_PATH = ART_DIR / "isolation_forest.pkl"


def _fit_one(group: pd.DataFrame) -> dict:
    """Fit a scaler + IsolationForest on one slice of normal training rows."""
    X = group[ML_FEATURES].to_numpy(dtype=float)
    # Guard against NaN/inf from any upstream edge rows.
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    # contamination is low: rogues are rare among the "normal" rows used to
    # fit (we train only on is_agent_anomaly==0 of the train split).
    model = IsolationForest(
        n_estimators=150,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(Xs)
    return {"model": model, "feature_names": list(ML_FEATURES), "scaler": scaler}


def main() -> int:
    if not DATA_PATH.exists():
        print(f"[err] {DATA_PATH} missing — run `python augment.py` first.")
        return 1
    df = pd.read_csv(DATA_PATH)
    train = df[df["split"] == "train"]
    # Train ONLY on normal rows (Phase 08B: unsupervised on 'unusual for this agent').
    train_normal = train[train["is_agent_anomaly"] == 0]

    agent_types = sorted(train["agent_type"].unique())
    ART_DIR.mkdir(parents=True, exist_ok=True)

    models = {}
    for atype in agent_types:
        slice_df = train_normal[train_normal["agent_type"] == atype]
        if len(slice_df) < 20:
            print(f"[skip] {atype}: only {len(slice_df)} normal rows")
            continue
        models[atype] = _fit_one(slice_df)
        # Quick self-report: how many of THIS type's own train rogues get flagged?
        rogue_slice = train[(train["agent_type"] == atype) & (train["is_agent_anomaly"] == 1)]
        if len(rogue_slice):
            Xr = np.nan_to_num(rogue_slice[ML_FEATURES].to_numpy(dtype=float))
            pred = models[atype]["model"].predict(models[atype]["scaler"].transform(Xr))
            flagged = int((pred == -1).sum())
            print(f"[ {atype:13s} ] trained on {len(slice_df):6d} normal rows | flagged {flagged}/{len(rogue_slice)} own rogues")

    # Default model: pooled across all types, used if an agent_type is unseen at serve time.
    default = _fit_one(train_normal) if len(train_normal) >= 50 else None

    artifact = {
        "models": models,
        "default": default,
        "feature_names": list(ML_FEATURES),
        "agent_types": agent_types,
        "version": "1.0",
    }
    with OUT_PATH.open("wb") as f:
        pickle.dump(artifact, f)
    print(f"[ok] wrote artifact -> {OUT_PATH}")
    print(f"     agent types: {list(models.keys())} (default={'yes' if default else 'no'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
