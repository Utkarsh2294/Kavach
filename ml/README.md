# Kavach ML / Intelligence Layer

Locally-trained classical models for real-time agent-transaction risk scoring.
**No external LLM / API calls anywhere in the decisioning path** — every
governance decision is a deterministic rule or a model loaded from disk at
startup, scored in-process with zero inference-time network calls.

## Pipeline

```
download_paysim.py   ──► data/paysim_raw.csv      (base dataset, PaySim-shaped)
augment.py           ──► data/augmented.csv        (rolling features + rogues)
train_isolation_forest.py ─► artifacts/isolation_forest.pkl   (per agent_type)
train_xgboost.py     ──► artifacts/xgboost_risk.pkl           (calibrated)
validate.py          ──► validation_report.md                 (real metrics)
features.py          ──► canonical feature contract (shared w/ backend serving)
```

## Run

```bash
cd ml
ML_SAMPLE_SIZE=120000 python download_paysim.py   # ~120k rows (synthetic fallback)
python augment.py                                # augmentation + rogues
python train_isolation_forest.py                 # artifacts/isolation_forest.pkl
python train_xgboost.py                          # artifacts/xgboost_risk.pkl + report
python validate.py                               # regenerate validation_report.md
```

## Key design decisions (Phase 08 spec)

1. **Balance-leakage fix** — raw PaySim balance columns are excluded from
   `features.ML_FEATURES`; `augment.py` engineers deltas/ratios instead.
2. **Per-agent rolling behavioral features** (not a global mean) — the model
   flags "unusual for THIS agent", matching the product's value prop.
3. **Validation split pre-dates rogue injection** — `augment.py` partitions
   agents into `train`/`val` by `agent_id` *before* injecting rogues, and
   injects train/val rogues with independent seeds, so validation metrics
   are not artificially easy.
4. **Zero network calls at inference** — both artifacts load once at FastAPI
   startup; `backend/app/services/scoring.score_transaction()` runs in-process.
5. **Shared feature contract** — `features.py` is the single source of truth
   for feature names & formulas used by both training and serving.

## Served RiskScore

`score_transaction(agent_id, transaction_features) -> RiskScore` returns:
`{"score": 0..1, "isolation_forest_flag": bool, "xgboost_score": float,
   "top_features": [(name, importance), ...]}`

Decision bands (mirrored in `backend/app/config.py`):
- `score < 0.30` → approve  (rules already passed)
- `0.30 ≤ score < 0.70` → escalate  (human review queue)
- `score ≥ 0.70` → deny

The XGBoost PR-AUC on the held-out independent-rogue validation split and
the Isolation Forest flag rate are reported in `validation_report.md`; both
are regenerated from real runs by `validate.py`.
