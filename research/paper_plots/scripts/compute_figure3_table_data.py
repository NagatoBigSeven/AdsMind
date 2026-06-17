#!/usr/bin/env python3
"""
Compute radar-chart table data for figure3_llm_performance.ipynb
from the raw all_variants_summary.csv files across 4 LLM backends.

Output: research/results/processed/figure3/radar_data.csv
  Columns: Variant, Mean_dE_vs_full_eV, Success_rate,
           Mean_4backend_range_eV, Agreement_rate
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent  # AdsMind repo root (scripts/ -> paper_plots/ -> research/ -> repo)

adsmind_dir = BASE / "research/results/basic_experiments/cmu20/adsmind"
backend_dirs = [
    "gpt54_mace_mp0_small",
    "grok4_mace_mp0_small",
    "gemini25pro_mace_mp0_small",
    "claude_sonnet46_mace_mp0_small",
]
out_dir = BASE / "research/results/processed/figure3"
out_dir.mkdir(parents=True, exist_ok=True)

AGREEMENT_THRESHOLD = 0.05  # eV — standard chemical accuracy

variant_map = {
    "one_shot": "1-Shot",
    "no_slip": "w/o Slip",
    "no_forbid": "w/o Forbid",
    "no_termination": "w/o Term",
    "full": "Full",
}
order = ["1-Shot", "w/o Slip", "w/o Forbid", "w/o Term", "Full"]

# ---------------------------------------------------------------------------
# 1. Load and clean all data
# ---------------------------------------------------------------------------
frames = []
for b in backend_dirs:
    f = pd.read_csv(adsmind_dir / b / "all_variants_summary.csv")
    frames.append(f)
df = pd.concat(frames, ignore_index=True)

df["best_energy"] = pd.to_numeric(df["best_energy"], errors="coerce")
df["delta_vs_full"] = pd.to_numeric(df["delta_vs_full"], errors="coerce")
df["success"] = df["success"].astype(str).str.upper().eq("TRUE")
df.loc[~df["success"], "best_energy"] = np.nan

# ---------------------------------------------------------------------------
# 2. Compute all metrics per variant in a single pass
# ---------------------------------------------------------------------------
rows = []
for vk, vn in variant_map.items():
    sub = df[df["variant"] == vk]

    # Table 1 metrics (aggregated across all 4 backends)
    mean_de = float(sub["delta_vs_full"].mean())
    success_rate = float(sub["success"].mean() * 100)

    # Table 3 metrics (cross-backend range per case)
    pivot = sub.pivot_table(index="case_id", columns="backend_key", values="best_energy", aggfunc="first")
    pivot_complete = pivot.dropna()  # only cases where all 4 backends succeeded
    ranges = pivot_complete.max(axis=1) - pivot_complete.min(axis=1)
    mean_range = float(ranges.mean()) if len(ranges) > 0 else np.nan
    n_total = len(ranges)
    agreement_rate = (ranges <= AGREEMENT_THRESHOLD).sum() / n_total if n_total > 0 else np.nan

    rows.append({
        "Variant": vn,
        "Mean_dE_vs_full_eV": round(mean_de, 3),
        "Success_rate": round(success_rate, 1),
        "Mean_4backend_range_eV": round(mean_range, 6),
        "Agreement_rate": round(agreement_rate, 6),
    })

df_merged = pd.DataFrame(rows).set_index("Variant").reindex(order).reset_index()
df_merged.to_csv(out_dir / "radar_data.csv", index=False)
print("Saved radar_data.csv")
print(df_merged.to_string(index=False))
