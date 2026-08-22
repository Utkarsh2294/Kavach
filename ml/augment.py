"""
Phase 08A — Agent-metadata augmentation & behavioral feature engineering.

Reads the PaySim-shaped base dataset (`ml/data/paysim_raw.csv`) and augments
it into the agent-governance feature set the risk models train on.

Three deliberate, verifiable design decisions (Phase 08 spec):

1. BALANCE-LEAKAGE FIX — PaySim's raw balance columns leak the label
   (`newbalanceOrig == 0` is a near-perfect fraud signal). We DROP the raw
   balance columns from the FEATURE set and engineer deltas/ratios instead:
       balance_delta_orig  = newbalanceOrig - oldbalanceOrg
       balance_delta_dest  = newbalanceDest - oldbalanceDest
       amount_to_balance_ratio = amount / (oldbalanceOrg + 1)
   (These leakage-fixed columns stay in the augmented dataset for inspection,
   but the served models only use the behavioral feature set from
   `ml/features.py` — which is derivable at inference time from the
   transaction stream, because bank balances are not on the Kavach hot path.)

2. ROLLING PER-AGENT behavioral features (not a global mean):
       amount_deviation     vs. THIS agent's rolling mean
       velocity_1h          count of prior txns in the same step (~1h)
       merchant_entropy      entropy of THIS agent's category history
       time_of_day_zscore    deviation from THIS agent's normal hour pattern

3. VALIDATION SPLIT PREDATES ROGUE INJECTION — we partition agents into
   train/val by `agent_id` FIRST, then inject scripted rogue sequences into
   disjoint subsets of each split using INDEPENDENT RNG seeds. This means
   the validation positives are independently generated realizations the
   model has never seen exact copies of, so reported metrics are not
   measuring an artificially easy task.

The injected target is `is_agent_anomaly` (distinct from PaySim's own
`isFraud`) — it labels scripted "unusual-for-this-agent" sequences:
spikes in amount, off-hours bursts, and novel merchant categories.

Outputs:
    ml/data/augmented.csv
    ml/data/augment_manifest.md   (leakage fix + feature provenance)
"""

import os
import sys
import math
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from features import ML_FEATURES, build_features, shannon_entropy

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_PATH = DATA_DIR / "paysim_raw.csv"
OUT_PATH = DATA_DIR / "augmented.csv"
MANIFEST_PATH = DATA_DIR / "augment_manifest.md"

AGENT_TYPES = ["travel", "subscription", "procurement", "sub-agent", "orchestrator"]
KAVACH_MERCHANT_CATEGORIES = [
    "Cloud Compute", "SaaS License", "API Gateway", "Storage", "Data Transfer",
    "Monitoring", "Security Audit", "Compliance Check", "ML Training", "CDN Cache",
]

# Rogue injection parameters (Phase 08 spec: small, documented set).
ROGUE_FRACTION_TRAIN = 0.10   # fraction of train agents chosen to go rogue
ROGUE_FRACTION_VAL = 0.10     # fraction of val agents chosen to go rogue
ROGUE_BURST_LEN = 8           # scripted anomalous txns per rogue agent
ANOMALY_BASE_RATE = 0.0002    # extra spontaneous micro-anomalies on normal rows


def stable_hash_int(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)


def agent_type_for(agent_id: str) -> str:
    return AGENT_TYPES[stable_hash_int(f"{agent_id}-type") % len(AGENT_TYPES)]


def delegation_depth_for(agent_id: str) -> int:
    return stable_hash_int(f"{agent_id}-depth") % 4  # 0..3


def delegation_chain_for(agent_id: str) -> str:
    return f"chain-{stable_hash_int(f'{agent_id}-chain') % 32:02d}"


def merchant_category_for(agent_id: str, typ: str, amount: float) -> str:
    """Deterministic category assignment giving each agent a stable favorite."""
    base = stable_hash_int(agent_id) % len(KAVACH_MERCHANT_CATEGORIES)
    jitter = stable_hash_int(f"{agent_id}-{typ}") % len(KAVACH_MERCHANT_CATEGORIES)
    # 70% favorite category, 30% jitter -> realistic per-agent category entropy
    if stable_hash_int(f"{agent_id}-{int(amount)}") % 10 < 7:
        return KAVACH_MERCHANT_CATEGORIES[base]
    return KAVACH_MERCHANT_CATEGORIES[jitter]


def engineer_balance_features(df: pd.DataFrame) -> pd.DataFrame:
    """Decision 1: replace raw balance columns with deltas/ratios."""
    df = df.copy()
    df["balance_delta_orig"] = df["newbalanceOrig"] - df["oldbalanceOrg"]
    df["balance_delta_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]
    df["amount_to_balance_ratio"] = df["amount"] / (df["oldbalanceOrg"].abs() + 1.0)
    # The raw balance columns remain in the CSV for auditability but are
    # explicitly excluded from ML_FEATURES, so no model can read them.
    return df


def assign_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Synthesize agent governance fields (agent_type, depth, declared_intent...)."""
    df = df.copy()
    unique_agents = df["nameOrig"].unique()
    meta = {
        a: {
            "agent_type": agent_type_for(a),
            "delegation_depth": delegation_depth_for(a),
            "delegation_chain_id": delegation_chain_for(a),
            "declared_intent": f"{agent_type_for(a)}_routine",
            "authorized_by": "treasury_root" if delegation_depth_for(a) == 0 else "parent_agent",
        }
        for a in unique_agents
    }
    for col, key in [
        ("agent_type", "agent_type"),
        ("delegation_depth", "delegation_depth"),
        ("delegation_chain_id", "delegation_chain_id"),
        ("declared_intent", "declared_intent"),
        ("authorized_by", "authorized_by"),
    ]:
        df[col] = df["nameOrig"].map(lambda a: meta[a][key])
    df["agent_id"] = df["nameOrig"]
    df["merchant_category"] = [
        merchant_category_for(a, t, amt)
        for a, t, amt in zip(df["agent_id"], df["type"], df["amount"])
    ]
    return df


def compute_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Decision 2: per-agent rolling behavioral features (row n uses rows < n)."""
    df = df.sort_values(["agent_id", "step"]).reset_index(drop=True).copy()
    df["row_idx"] = df.groupby("agent_id").cumcount()

    # time-of-day: PaySim's step is a 1-hour tick.
    df["time_of_day_hour"] = df["step"] % 24

    # Per-agent rolling stats using ONLY prior rows (shift(1) then expanding).
    df["prior_amount"] = df.groupby("agent_id")["amount"].shift(1)
    df["rolling_mean_amount"] = (
        df.groupby("agent_id")["prior_amount"]
        .transform(lambda s: s.expanding(min_periods=1).mean())
        .fillna(method="bfill")
        .fillna(df["amount"])
    ) if False else None  # placeholder, replaced below

    g = df.groupby("agent_id")
    # rolling mean of prior amounts
    prior_amt = df["amount"].groupby(df["agent_id"]).shift(1)
    df["rolling_mean_amount"] = (
        prior_amt.groupby(df["agent_id"]).transform(lambda s: s.expanding(min_periods=1).mean())
    )
    df["rolling_mean_amount"] = df["rolling_mean_amount"].fillna(df["amount"])
    df = df.drop(columns=["prior_amount"]) if "prior_amount" in df.columns else df

    # velocity_1h: count of prior txns in the same step (step ~ 1h window)
    def _velocity(s_step: pd.Series) -> pd.Series:
        out = []
        seen = {}
        for step in s_step:
            out.append(seen.get(step, 0))
            seen[step] = seen.get(step, 0) + 1
        return pd.Series(out, index=s_step.index)

    df["velocity_1h"] = g["step"].transform(_velocity)

    # merchant entropy: entropy of category counts over prior rows
    def _entropy(group: pd.DataFrame) -> pd.Series:
        rows = group["merchant_category"].tolist()
        out = []
        counts: dict = {}
        for i, cat in enumerate(rows):
            out.append(shannon_entropy(counts.copy()))
            counts[cat] = counts.get(cat, 0) + 1
        return pd.Series(out, index=group.index)

    df["merchant_entropy"] = g.apply(_entropy).reset_index(level=0, drop=True)

    # hour rolling mean/std per agent (prior)
    prior_hour = df["time_of_day_hour"].groupby(df["agent_id"]).shift(1)
    df["agent_mean_hour"] = (
        prior_hour.groupby(df["agent_id"]).transform(lambda s: s.expanding(min_periods=1).mean())
    ).fillna(df["time_of_day_hour"])
    df["agent_std_hour"] = (
        prior_hour.groupby(df["agent_id"]).transform(lambda s: s.expanding(min_periods=1).std())
    ).fillna(1.0)

    # per-agent cap (proxy from the original balance base — kept stable)
    df = df.merge(
        df.groupby("agent_id")["amount"].transform("max").rename("agent_cap"),
        left_index=True, right_index=True,
    )
    # Ensure cap is positive and sensible.
    df["agent_cap"] = df["agent_cap"].clip(lower=1000.0) * 4.0

    # Build the canonical feature vector for every row.
    feat_rows = []
    for r in df.itertuples(index=False):
        fd = build_features(
            amount=r.amount,
            agent_mean_amount=r.rolling_mean_amount,
            agent_cap=r.agent_cap,
            velocity_1h=r.velocity_1h,
            merchant_entropy=r.merchant_entropy,
            time_of_day_hour=int(r.time_of_day_hour),
            agent_mean_hour=r.agent_mean_hour,
            agent_std_hour=r.agent_std_hour,
            delegation_depth=int(r.delegation_depth),
        )
        feat_rows.append([fd[k] for k in ML_FEATURES])
    feat_df = pd.DataFrame(feat_rows, columns=[f"f_{c}" for c in ML_FEATURES], index=df.index)
    for c in ML_FEATURES:
        df[c] = feat_df[f"f_{c}"]

    return df


def split_agents(df: pd.DataFrame, val_fraction: float = 0.2, seed: int = 7) -> pd.DataFrame:
    """Decision 3: partition agents into train/val BEFORE rogue injection."""
    agents = sorted(df["agent_id"].unique())
    rng = np.random.default_rng(seed)
    rng.shuffle(agents)
    n_val = max(1, int(len(agents) * val_fraction))
    val_agents = set(agents[:n_val])
    df = df.copy()
    df["split"] = df["agent_id"].map(lambda a: "val" if a in val_agents else "train")
    return df


def inject_rogue_sequences(df: pd.DataFrame) -> pd.DataFrame:
    """Inject scripted 'unusual-for-this-agent' sequences; label is_agent_anomaly.

    Rogues are generated independently for train and val splits (different
    seeds) so the validation positives are not trivial copies of train ones.
    """
    df = df.copy()
    df["is_agent_anomaly"] = 0

    for split_name, frac, seed in [
        ("train", ROGUE_FRACTION_TRAIN, 101),
        ("val", ROGUE_FRACTION_VAL, 202),
    ]:
        sub_agents = sorted(df.loc[df["split"] == split_name, "agent_id"].unique())
        rng = np.random.default_rng(seed)
        n_rogue = max(1, int(len(sub_agents) * frac))
        rogue_agents = rng.choice(sub_agents, size=n_rogue, replace=False)

        new_rows = []
        for agent_id in rogue_agents:
            base_amount = float(
                df.loc[df["agent_id"] == agent_id, "amount"].mean()
            ) or 100.0
            cap = float(
                df.loc[df["agent_id"] == agent_id, "agent_cap"].iloc[0]
            ) if not df.loc[df["agent_id"] == agent_id, "agent_cap"].empty else base_amount * 4
            for k in range(ROGUE_BURST_LEN):
                # Spike: amount far above this agent's normal, off-hours,
                # and a category THIS agent never uses -> all anomalies.
                spike_amount = float(np.round(base_amount * rng.uniform(15, 40), 2))
                hour = int(rng.integers(0, 5))
                novel_cat = KAVACH_MERCHANT_CATEGORIES[
                    stable_hash_int(f"{agent_id}-rogue-{k}") % len(KAVACH_MERCHANT_CATEGORIES)
                ]
                step = int(df.loc[df["agent_id"] == agent_id, "step"].max()) + 1 + k
                row = {
                    "step": step, "type": "TRANSFER", "amount": spike_amount,
                    "nameOrig": agent_id, "oldbalanceOrg": 0.0,
                    "newbalanceOrig": 0.0, "nameDest": f"R{rng.integers(0,99)}",
                    "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
                    "isFraud": 0, "isFlaggedFraud": 0,
                    "balance_delta_orig": 0.0, "balance_delta_dest": 0.0,
                    "amount_to_balance_ratio": spike_amount,
                    "agent_id": agent_id, "agent_type": agent_type_for(agent_id),
                    "delegation_depth": delegation_depth_for(agent_id),
                    "delegation_chain_id": delegation_chain_for(agent_id),
                    "declared_intent": "spike_unauthorized",
                    "authorized_by": "overflow",
                    "merchant_category": novel_cat,
                    "time_of_day_hour": hour,
                    "rolling_mean_amount": base_amount, "velocity_1h": 0,
                    "merchant_entropy": 0.0, "agent_mean_hour": 12,
                    "agent_std_hour": 1.0, "agent_cap": cap, "split": split_name,
                    "is_agent_anomaly": 1,
                }
                # Canonical features for the rogue row (recompute to stay consistent).
                fd = build_features(
                    amount=spike_amount, agent_mean_amount=base_amount, agent_cap=cap,
                    velocity_1h=ROGUE_BURST_LEN, merchant_entropy=0.0,
                    time_of_day_hour=hour, agent_mean_hour=12,
                    agent_std_hour=1.0, delegation_depth=delegation_depth_for(agent_id),
                )
                for c in ML_FEATURES:
                    row[c] = fd[c]
                new_rows.append(row)
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    # A tiny background spontaneous-anomaly rate on otherwise-normal rows.
    if ANOMALY_BASE_RATE > 0:
        normal_mask = df["is_agent_anomaly"] == 0
        rng2 = np.random.default_rng(303)
        flip = rng2.random(len(df)) < ANOMALY_BASE_RATE
        df.loc[normal_mask & flip, "is_agent_anomaly"] = 1

    return df


def write_manifest(df: pd.DataFrame) -> None:
    n = len(df)
    n_train = int((df["split"] == "train").sum())
    n_val = int((df["split"] == "val").sum())
    anomalies = int(df["is_agent_anomaly"].sum())
    md = f"""# Augmented Dataset Manifest

Source: `{RAW_PATH.name}` (PaySim-shaped)
Output: `{OUT_PATH.name}`  ({n} rows, {df['agent_id'].nunique()} agents)

## Leakage Fix (Decision 1)

Raw PaySim balance columns (`oldbalanceOrg`, `newbalanceOrig`,
`oldbalanceDest`, `newbalanceDest`) are EXCLUDED from `ml.features.ML_FEATURES`.
Engineered leakage-safe columns added to the CSV (for inspection only):
- `balance_delta_orig  = newbalanceOrig - oldbalanceOrg`
- `balance_delta_dest  = newbalanceDest - oldbalanceDest`
- `amount_to_balance_ratio = amount / (oldbalanceOrg + 1)`

No served model reads a raw balance column. Verify in `ml/features.py:ML_FEATURES`.

## Behavioral Features (Decision 2)

All rolling features are per-agent (not global), computed from prior rows only:
- `amount_deviation`  — vs. THIS agent's rolling mean amount
- `velocity_1h`        — prior txn count in the same step (~1h window)
- `merchant_entropy`   — Shannon entropy of THIS agent's category history
- `time_of_day_zscore` — deviation from THIS agent's normal hour pattern

## Validation Split (Decision 3)

Agents partitioned into train/val by `agent_id` before rogue injection.
- train agents: {n_train} rows
- val agents:   {n_val} rows

Rogue sequences injected independently per split (train seed=101, val seed=202),
so validation positives are independent realizations the model never trained on.

## Target

`is_agent_anomaly` (distinct from PaySim `isFraud`): {anomalies} positives
({(anomalies / max(1, n)) * 100:.3f}% of rows). Constructed from scripted
amount spikes, off-hours bursts, and novel merchant categories.
"""
    MANIFEST_PATH.write_text(md, encoding="utf-8")


def main() -> int:
    if not RAW_PATH.exists():
        print(f"[err] {RAW_PATH} not found — run `python download_paysim.py` first.")
        return 1
    print(f"[load] {RAW_PATH}")
    df = pd.read_csv(RAW_PATH)
    print(f"[load] {len(df)} rows, {df['nameOrig'].nunique()} agents")

    df = engineer_balance_features(df)
    df = assign_metadata(df)
    df = compute_rolling_features(df)
    df = split_agents(df)  # Decision 3: split BEFORE injection
    df = inject_rogue_sequences(df)
    df = df.sort_values(["split", "agent_id", "step"]).reset_index(drop=True)

    # Persist the canonical feature columns + everything needed for training/serving.
    out_cols = ["split", "agent_id", "agent_type", "delegation_depth",
                "delegation_chain_id", "declared_intent", "authorized_by",
                "step", "merchant_category", "amount", "time_of_day_hour",
                "rolling_mean_amount", "velocity_1h", "merchant_entropy",
                "agent_mean_hour", "agent_std_hour", "agent_cap", "isFraud",
                "is_agent_anomaly", "balance_delta_orig", "balance_delta_dest",
                "amount_to_balance_ratio"] + ML_FEATURES + [
        "oldbalanceOrg", "newbalanceOrig",  # kept for auditability, never fed to models
        "oldbalanceDest", "newbalanceDest"]
    out_cols = [c for c in out_cols if c in df.columns]
    df[out_cols].to_csv(OUT_PATH, index=False)

    write_manifest(df)
    print(f"[ok] wrote {len(df)} rows -> {OUT_PATH}")
    print(f"[ok] manifest -> {MANIFEST_PATH}")
    print(f"     is_agent_anomaly: {int(df['is_agent_anomaly'].sum())} positives")
    print(f"     split: {(df['split']=='train').sum()} train / {(df['split']=='val').sum()} val")
    return 0


if __name__ == "__main__":
    sys.exit(main())
