#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "OPENROUTER_API_KEY is not set" >&2
  exit 1
fi

MANIFEST="research/agent_eval/manifests/ocd_gmae_manifest.csv"
CONFIG="research/agent_eval/configs/frozen_config_gemini25pro_openrouter.json"
ABLATION_DIR="research/results/ocd_gmae_gemini_ablation_v1"
ONE_SHOT_DIR="research/results/ocd_gmae_v1_gemini_one_shot"
CASES_ALL="003,004,023,024,005,019,015,013,012,016"
CASES_FULL="012,016"
VARIANTS_ALL="full,no_slip,no_forbid,no_termination,single_shot"

python -m research.agent_eval.run_ablation \
  --manifest "$MANIFEST" \
  --config "$CONFIG" \
  --output "$ABLATION_DIR" \
  --cases "$CASES_FULL" \
  --variants full

python -m research.agent_eval.run_ablation \
  --manifest "$MANIFEST" \
  --config "$CONFIG" \
  --output "$ABLATION_DIR" \
  --cases "$CASES_ALL" \
  --variants no_slip

python -m research.agent_eval.run_ablation \
  --manifest "$MANIFEST" \
  --config "$CONFIG" \
  --output "$ABLATION_DIR" \
  --cases "$CASES_ALL" \
  --variants no_forbid

python -m research.agent_eval.run_ablation \
  --manifest "$MANIFEST" \
  --config "$CONFIG" \
  --output "$ABLATION_DIR" \
  --cases "$CASES_ALL" \
  --variants no_termination

python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir "$ABLATION_DIR" \
  --one-shot-dir "$ONE_SHOT_DIR" \
  --cases "$CASES_ALL" \
  --variants "$VARIANTS_ALL"

python -m research.agent_eval.summarize_multi_backend_ablation \
  --summary gemini="$ABLATION_DIR/ablation_summary.csv" \
  --summary grok="research/results/ocd_gmae_xai_grok4_ablation_v1/ablation_summary.csv" \
  --summary gpt54="research/results/ocd_gmae_openai_gpt54_ablation_v1/ablation_summary.csv" \
  --summary claude="research/results/ocd_gmae_anthropic_sonnet46_ablation_v1/ablation_summary.csv" \
  --output-csv "research/results/ocd_gmae_ablation_multi_backend_final.csv" \
  --output-json "research/results/ocd_gmae_ablation_multi_backend_final.json"

python - <<'PY'
import csv
from pathlib import Path

case_ids = ["003", "004", "023", "024", "005", "019", "015", "013", "012", "016"]
one_shot_paths = {
    "gemini": Path("research/results/ocd_gmae_v1_gemini_one_shot/summary.csv"),
    "grok": Path("research/results/ocd_gmae_v1_xai_grok4_one_shot/summary.csv"),
    "gpt54": Path("research/results/ocd_gmae_v1_openai_gpt54_one_shot/summary.csv"),
    "claude": Path("research/results/ocd_gmae_v1_anthropic_sonnet46_one_shot/summary.csv"),
}
final_path = Path("research/results/ocd_gmae_ablation_multi_backend_final.csv")
out_path = Path("research/results/ocd_gmae_ablation_final_vs_one_shot_4backend.csv")


def parse_float(value: str | None) -> float | None:
    if value in (None, "", "None"):
        return None
    return float(value)


one_shot = {}
for label, path in one_shot_paths.items():
    for row in csv.DictReader(path.open()):
        energy = parse_float(row.get("best_energy_eV")) if row.get("status") == "success" else None
        one_shot.setdefault(row["case_id"], {})[label] = energy

ablation_rows = {(row["case_id"], row["variant"]): row for row in csv.DictReader(final_path.open())}
rows = []
for case_id in case_ids:
    energies = [value for value in one_shot.get(case_id, {}).values() if value is not None]
    one_shot_range = max(energies) - min(energies) if len(energies) >= 2 else None
    best_variant = None
    best_range = None
    for variant in ["full", "no_slip", "no_forbid", "no_termination"]:
        row = ablation_rows[(case_id, variant)]
        range_best_energy = parse_float(row.get("range_best_energy"))
        if range_best_energy is None:
            continue
        if best_range is None or range_best_energy < best_range:
            best_variant = variant
            best_range = range_best_energy
    rows.append(
        {
            "case_id": case_id,
            "one_shot_range_4backend": one_shot_range,
            "best_closed_loop_variant_4backend": best_variant,
            "best_closed_loop_range_4backend": best_range,
            "range_delta_vs_one_shot_4backend": (
                None if one_shot_range is None or best_range is None else best_range - one_shot_range
            ),
        }
    )

with out_path.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(out_path)
for row in rows:
    print(row)
PY
