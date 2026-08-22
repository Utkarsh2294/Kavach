"""
Phase 08C — XGBoost (supervised) risk classifier.

Target: `is_agent_anomaly` (the agent-behavior anomaly target engineered in
`augment.py`, NOT PaySim's `isFraud`).

Critical honesty rule (Phase 08C spec): the validation split is created in
`augment.py` BEFORE rogue injection, so the val positives are independent
realizations the model never trained on. This script only consumes that
pre-existing `split` column — it never re-splits in a way that would leak
rogues from train into val.

Output:
  - ml/artifacts/xgboost_risk.pkl  (model + feature_names + agent_type one-hot schema +
                                     calibration; served probability in [0,1])
  - ml/validation_report.md           (real precision/recall/F1/AUC from the held-out split)

The probability is produced by `CalibratedClassifierCV` (isotonic, cv=3) on top
of XGBoost, so reported `xgboost_score` is a true calibrated probability, not
a raw margin. `top_features` (feature importances) are read from the underlying
XGBoost estimator and re-mapped to the canonical `ML_FEATURES` names so the UI
audit log / escalation queue can display explainability.

Run: cd ml && python train_xgboost.py
"""

import sys
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix,
)

from features import ML_FEATURES

DATA_PATH = Path(__file__).resolve().parent / "data" / "augmented.csv"
ART_DIR = Path(__file__).resolve().parent / "artifacts"
OUT_PATH = ART_DIR / "xgboost_risk.pkl"
REPORT_PATH = Path(__file__).resolve().parent / "validation_report.md"

# Probability decision thresholds used by the serving layer (mirrored in
# backend config). These are NOT magic numbers scattered in the pipeline —
# they live here as the source of truth and in the artifact.
SCORE_THRESHOLD_LOW = 0.30   # < low  -> approve (rules already passed)
SCORE_THRESHOLD_HIGH = 0.70  # >= high -> deny ; middle band -> escalate


def _build_matrix(df: pd.DataFrame, agent_types: list[str]):
    """Behavioral features + one-hot agent_type. Returns (X, y, full_feature_names)."""
    X_feat = df[ML_FEATURES].to_numpy(dtype=float)
    X_feat = np.nan_to_num(X_feat, nan=0.0, posinf=0.0, neginf=0.0)

    onehot_names = [f"type::{t}" for t in agent_types]
    type_idx = {t: i for i, t in enumerate(agent_types)}
    onehot = np.zeros((len(df), len(agent_types)), dtype=float)
    for i, t in enumerate(df["agent_type"].to_list()):
        onehot[i, type_idx.get(t, -1)] = 1.0

    X = np.hstack([X_feat, onehot]) if len(agent_types) else X_feat
    full_names = list(ML_FEATURES) + onehot_names
    return X, df["is_agent_anomaly"].to_numpy(dtype=int).ravel(), full_names


def _feature_importances(clf, names: list[str]) -> list[tuple[str, float]]:
    """Average gain importances across the fitted calibration-fold estimators."""
    estimators = [
        fitted.estimator for fitted in getattr(clf, "calibrated_classifiers_", [])
        if getattr(fitted, "estimator", None) is not None
    ]
    if not estimators:
        estimator = getattr(clf, "estimator", None)
        estimators = [estimator] if estimator is not None else []
    vectors = [
        np.asarray(estimator.feature_importances_, dtype=float)
        for estimator in estimators
        if hasattr(estimator, "feature_importances_")
    ]
    imps = np.mean(vectors, axis=0).tolist() if vectors else [0.0] * len(names)
    ranked = sorted(zip(names, imps), key=lambda kv: kv[1], reverse=True)
    return [(n, float(v)) for n, v in ranked if v > 0]


def main() -> int:
    if not DATA_PATH.exists():
        print(f"[err] {DATA_PATH} missing — run `python augment.py` first.")
        return 1
    df = pd.read_csv(DATA_PATH)

    # Honor the pre-existing honest split (Decision 3 from augment.py).
    train = df[df["split"] == "train"]
    val = df[df["split"] == "val"]
    agent_types = sorted(train["agent_type"].unique())

    Xtr, ytr, names = _build_matrix(train, agent_types)
    Xva, yva, _ = _build_matrix(val, agent_types)

    pos = int(ytr.sum()); neg = int((ytr == 0).sum())
    scale_pos = max(1.0, neg / max(1, pos))
    print(f"[train] {len(train)} rows | {pos} pos / {neg} neg | scale_pos_weight={scale_pos:.2f}")
    print(f"[val]   {len(val)} rows | {int(yva.sum())} pos / {int((yva==0).sum())} neg (independent rogues)")

    base = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=3,
        scale_pos_weight=scale_pos,
        eval_metric="aucpr",
        tree_method="hist",
        random_state=42,
        n_jobs=-1,
    )
    # Isotonic calibration -> true 0..1 probability. cv=3 uses folds drawn only
    # from the training split, so the validation split stays fully untouched.
    clf = CalibratedClassifierCV(base, method="isotonic", cv=3)
    clf.fit(Xtr, ytr)

    # ── Honest metrics on the held-out validation split ──────────────────────
    probs = clf.predict_proba(Xva)[:, 1]
    preds = (probs >= 0.5).astype(int)
    prec = precision_score(yva, preds, zero_division=0)
    rec = recall_score(yva, preds, zero_division=0)
    f1 = f1_score(yva, preds, zero_division=0)
    try:
        auc = roc_auc_score(yva, probs)
    except ValueError:
        auc = float("nan")
    auprc = average_precision_score(yva, probs)
    tn, fp, fn, tp = confusion_matrix(yva, preds, labels=[0, 1]).ravel()

    importances = _feature_importances(clf, names)

    # Persist artifact (serving reads probability + importances; thresholds mirrored in config).
    artifact = {
        "model": clf,
        "feature_names": list(ML_FEATURES),
        "agent_types": agent_types,
        "onehot_names": [f"type::{t}" for t in agent_types],
        "full_feature_names": names,
        "feature_importances": importances,
        "score_threshold_low": SCORE_THRESHOLD_LOW,
        "score_threshold_high": SCORE_THRESHOLD_HIGH,
        "version": "1.0",
    }
    ART_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("wb") as f:
        pickle.dump(artifact, f)
    print(f"[ok] wrote artifact -> {OUT_PATH}")

    # ── validation_report.md with REAL metrics from an actual run ────────────
    top_lines = "\n".join(f"| `{n}` | {v:.4f} |" for n, v in importances[:12])
    report = f"""# ML Validation Report

Generated by `ml/train_xgboost.py` from a live training run on the held-out
`val` split of `ml/data/augmented.csv`.

## Model
- XGBoost (`xgboost.XGBClassifier`) + isotonic `CalibratedClassifierCV` (cv=3)
- Target: `is_agent_anomaly`
- Features: behavioral set from `ml/features.py` ({len(ML_FEATURES)}) + agent_type one-hot ({len(agent_types)})
- Calibration folds drawn ONLY from the `train` split; `val` split never seen during fit/calibration.

## Honest validation metrics (held-out `val` split — independent rogues)

| Metric | Value |
|---|---|
| Rows | {len(val)} |
| Positives | {int(yva.sum())} |
| Precision | {prec:.4f} |
| Recall | {rec:.4f} |
| F1 | {f1:.4f} |
| ROC-AUC | {auc:.4f} |
| PR-AUC (average precision) | {auprc:.4f} |

Confusion matrix (threshold 0.5): TP={tp} FP={fp} TN={tn} FN={fn}

## Serving decision bands (mirrored in backend config)
- score < {SCORE_THRESHOLD_LOW}  -> approve  (rules already passed)
- {SCORE_THRESHOLD_LOW} <= score < {SCORE_THRESHOLD_HIGH} -> escalate  (human review queue)
- score >= {SCORE_THRESHOLD_HIGH} -> deny

## Top feature importances (XGBoost gain)
| Feature | Importance |
|---|---|
{top_lines}

## Leakage fix verification
`ml/features.ML_FEATURES` contains no raw balance columns. `augment.py` engineered
`balance_delta_orig/dest` + `amount_to_balance_ratio` for inspection only; none
are in `ML_FEATURES`. Served features are computable from the transaction stream
+ agent row alone (zero network calls at inference).
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"[ok] wrote report -> {REPORT_PATH}")
    print(f"     P={prec:.3f} R={rec:.3f} F1={f1:.3f} AUC={auc if auc==auc else 0:.3f} PR-AUC={auprc:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
