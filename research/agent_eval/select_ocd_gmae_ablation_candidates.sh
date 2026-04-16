#!/usr/bin/env bash
set -euo pipefail

TOP_N="${1:-10}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "No usable Python interpreter found." >&2
  exit 1
fi

GEMINI_SUMMARY="${GEMINI_SUMMARY:-research/results/ocd_gmae_v1_gemini_one_shot/summary.csv}"
GROK_SUMMARY="${GROK_SUMMARY:-research/results/ocd_gmae_v1_xai_grok4_one_shot/summary.csv}"
GPT54_SUMMARY="${GPT54_SUMMARY:-research/results/ocd_gmae_v1_openai_gpt54_one_shot/summary.csv}"
CLAUDE_SUMMARY="${CLAUDE_SUMMARY:-research/results/ocd_gmae_v1_anthropic_sonnet46_one_shot/summary.csv}"
RANK_CSV="${RANK_CSV:-research/results/ocd_gmae_one_shot_range_ranking.csv}"
RANK_JSON="${RANK_JSON:-research/results/ocd_gmae_one_shot_range_ranking.json}"
TOP_IDS="${TOP_IDS:-research/results/ocd_gmae_one_shot_top_${TOP_N}_case_ids.txt}"

"$PYTHON_BIN" -m research.agent_eval.rank_one_shot_ranges \
  --summary gemini="$GEMINI_SUMMARY" \
  --summary grok="$GROK_SUMMARY" \
  --summary gpt54="$GPT54_SUMMARY" \
  --summary claude="$CLAUDE_SUMMARY" \
  --output-csv "$RANK_CSV" \
  --output-json "$RANK_JSON" \
  --require-success

"$PYTHON_BIN" - "$TOP_N" "$RANK_CSV" "$TOP_IDS" <<'PY'
import csv
import sys
from pathlib import Path

top_n = int(sys.argv[1])
rank_csv = Path(sys.argv[2])
out_path = Path(sys.argv[3])

with rank_csv.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

case_ids = [row["case_id"] for row in rows[:top_n]]
out_path.write_text(",".join(case_ids) + "\n", encoding="utf-8")
print(f"Top {top_n} case ids: {','.join(case_ids)}")
print(f"Wrote {out_path}")
PY
