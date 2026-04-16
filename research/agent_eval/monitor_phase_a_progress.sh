#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

declare -a RUN_DIRS=(
  "gemini_ablation_v1"
  "xai_ablation_v2"
  "openai_gpt54_ablation_v1"
  "anthropic_sonnet46_ablation_v1"
)

declare -a VARIANTS=(
  "full"
  "no_slip"
  "no_forbid"
  "no_termination"
)

for run_dir in "${RUN_DIRS[@]}"; do
  echo "=== ${run_dir} ==="
  for variant in "${VARIANTS[@]}"; do
    variant_dir="research/results/${run_dir}/${variant}"
    if [[ -d "$variant_dir" ]]; then
      count="$(find "$variant_dir" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
    else
      count="0"
    fi
    printf "  %-15s %s\n" "${variant}:" "$count"
  done
done
