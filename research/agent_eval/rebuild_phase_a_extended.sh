#!/usr/bin/env bash
set -euo pipefail

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

CASES="01,02,04,05,09,10,12,13,14,15,16,17,18,19,20"
VARIANTS="full,no_slip,no_forbid,no_termination,single_shot"

declare -a PAIRS=(
  "gemini_ablation_v1:cmu_v1_gemini_one_shot"
  "xai_ablation_v2:cmu_v1_xai_progressive_one_shot"
  "openai_gpt54_ablation_v1:cmu_v1_openai_gpt54_one_shot"
  "anthropic_sonnet46_ablation_v1:cmu_v1_anthropic_sonnet46_one_shot"
)

for pair in "${PAIRS[@]}"; do
  IFS=":" read -r ABLATION_DIR ONE_SHOT_DIR <<< "$pair"
  echo "=== Rebuilding ${ABLATION_DIR} ==="
  "$PYTHON_BIN" -m research.agent_eval.rebuild_ablation_summary \
    --ablation-dir "research/results/${ABLATION_DIR}" \
    --one-shot-dir "research/results/${ONE_SHOT_DIR}" \
    --cases "$CASES" \
    --variants "$VARIANTS"
done
