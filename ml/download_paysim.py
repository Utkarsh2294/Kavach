"""
Phase 08A — Base dataset acquisition for the Kavach ML pipeline.

Reference dataset: PaySim (Kaggle, `ealaxi/paysim1`) — ~6.3M synthetic
mobile-money transactions with a realistic ~0.13% fraud rate.

This script tries the real Kaggle download first (if `kaggle.json` is
present), then falls back to a deterministic PaySim-shaped SYNTHETIC
generator. The fallback exists so the full pipeline can run end-to-end in
any environment without network access or Kaggle credentials — it produces
the EXACT same column schema and a comparable fraud-rate signal so
augment.py / train_*.py are dataset-agnostic.

Output: ml/data/paysim_raw.csv  (PaySim columns below)

PaySim columns:
    step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig,
    nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud

`step` is a synthetic 1-hour timestep. `type` ∈ {PAYMENT, TRANSFER,
CASH_OUT, DEBIT, CASH_IN}. `nameOrig` is reused as the proxy `agent_id`
during augmentation.

Run:
    cd ml && python download_paysim.py
    # or override size: ML_SAMPLE_SIZE=150000 python download_paysim.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_PATH = DATA_DIR / "paysim_raw.csv"

PAYSIM_TYPES = ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]
MERCHANT_CATEGORIES = [
    "Cloud Compute", "SaaS License", "API Gateway", "Storage", "Data Transfer",
    "Monitoring", "Security Audit", "Compliance Check", "ML Training", "CDN Cache",
]


def try_kaggle_download(out_path: Path) -> bool:
    """Attempt a real Kaggle download. Returns True on success."""
    creds = os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    if not creds and not Path.home().joinpath(".kaggle/kaggle.json").exists():
        return False
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi  # type: ignore

        api = KaggleApi()
        api.authenticate()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(
            "ealaxi/paysim1", path=str(DATA_DIR), unzip=True
        )
        downloaded = list(DATA_DIR.glob("*.csv"))
        # Rename the real PaySim CSV to our canonical path.
        for p in downloaded:
            if p != out_path and p.suffix == ".csv":
                p.rename(out_path)
        return out_path.exists()
    except Exception as exc:  # pragma: no cover - depends on kaggle creds
        print(f"[kaggle] download failed ({exc}); falling back to synthetic data.")
        return False


def generate_synthetic(n_rows: int, seed: int = 42) -> pd.DataFrame:
    """
    Deterministic PaySim-shaped synthetic generator.

    Produces ~0.13% fraud rows to match the real PaySim fraud rate, and
    injects a realistic per-agent behavioral signature so the downstream
    models have structure to learn (not pure noise).
    """
    rng = np.random.default_rng(seed)

    # ~3000 proxy agents; transactions are clustered per-agent.
    n_agents = max(1, n_rows // 40)
    agent_ids = [f"C{i}" for i in range(n_agents)]

    # Each agent has a stable behavioral profile.
    agent_base_amount = rng.lognormal(mean=4.0, sigma=1.0, size=n_agents) + 10.0
    agent_cap = rng.uniform(2000.0, 50000.0, size=n_agents)
    agent_preferred_hour = rng.integers(7, 20, size=n_agents)
    agent_txn_rate = rng.poisson(lam=3, size=n_agents) + 2  # txns per step

    rows = []
    n_steps = max(1, n_rows // (n_agents * 2))
    for step in range(n_steps):
        for ai in range(n_agents):
            count = int(agent_txn_rate[ai])
            for _ in range(count):
                typ = rng.choice(PAYSIM_TYPES, p=[0.5, 0.15, 0.2, 0.1, 0.05])
                base = float(agent_base_amount[ai])
                amount = float(np.round(max(0.1, rng.normal(base, base * 0.35)), 2))
                oldbal = float(np.round(max(0.0, rng.normal(base * 8, base * 2)), 2))
                newbal = float(np.round(max(0.0, oldbal - amount), 2))
                hour = int((agent_preferred_hour[ai] + rng.normal(0, 1.5)) % 24)
                dest = rng.choice(agent_ids) if rng.random() < 0.4 else f"M{rng.integers(0, 500)}"
                olddest = float(np.round(max(0.0, rng.normal(base * 3, base)), 2))
                newdest = float(np.round(max(0.0, olddest + amount), 2))
                isfraud = int(rng.random() < 0.0013)
                if isfraud:
                    # Fraudulent rows: huge amount relative to base, late hour.
                    amount = float(np.round(base * rng.uniform(20, 80), 2))
                    typ = "TRANSFER"
                    hour = int(rng.integers(0, 5))
                    newbal = 0.0
                rows.append((
                    step, typ, amount, agent_ids[ai], oldbal, newbal,
                    dest, olddest, newdest, isfraud, 0,
                ))

    cols = [
        "step", "type", "amount", "nameOrig", "oldbalanceOrg",
        "newbalanceOrig", "nameDest", "oldbalanceDest",
        "newbalanceDest", "isFraud", "isFlaggedFraud",
    ]
    df = pd.DataFrame(rows, columns=cols)

    # Trim to requested size if the generator overshot.
    if len(df) > n_rows:
        df = df.sample(n=n_rows, random_state=seed).sort_values("step").reset_index(drop=True)
    return df


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    n_rows = int(os.environ.get("ML_SAMPLE_SIZE", "120000"))

    if try_kaggle_download(OUT_PATH):
        print(f"[ok] downloaded real PaySim dataset -> {OUT_PATH}")
        return 0

    print(f"[gen] generating {n_rows} synthetic PaySim-shaped rows...")
    df = generate_synthetic(n_rows, seed=42)
    df.to_csv(OUT_PATH, index=False)
    fraud_rate = df["isFraud"].mean() * 100 if "isFraud" in df else float("nan")
    print(
        f"[ok] wrote {len(df)} rows to {OUT_PATH} "
        f"(fraud rate: {fraud_rate:.3f}%, agents: {df['nameOrig'].nunique()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
