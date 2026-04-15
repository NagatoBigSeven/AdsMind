#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MANIFEST_PATH="${MANIFEST_PATH:-research/agent_eval/manifests/ocd_gmae_manifest.csv}"
if [[ -f "$MANIFEST_PATH" ]]; then
  TOTAL_CASES="$(tail -n +2 "$MANIFEST_PATH" | wc -l | tr -d ' ')"
else
  TOTAL_CASES="unknown"
fi

declare -a RUN_DIRS=(
  "ocd_gmae_v1_gemini_one_shot"
  "ocd_gmae_v1_xai_grok4_one_shot"
  "ocd_gmae_v1_openai_gpt54_one_shot"
  "ocd_gmae_v1_anthropic_sonnet46_one_shot"
)

echo "Manifest cases: ${TOTAL_CASES}"
for run_dir in "${RUN_DIRS[@]}"; do
  target="research/results/${run_dir}"
  if [[ -d "$target" ]]; then
    completed="$(find "$target" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
  else
    completed="0"
  fi
  printf "%-40s %s\n" "${run_dir}:" "$completed"
done

if command -v tmux >/dev/null 2>&1; then
  echo
  tmux ls 2>/dev/null | grep 'ocd_.*_os' || true
fi
