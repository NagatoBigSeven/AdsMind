#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required but not installed." >&2
  exit 1
fi

MANIFEST_PATH="${MANIFEST_PATH:-research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv}"
declare -a BACKENDS=("gemini" "grok" "gpt54" "claude")

for backend in "${BACKENDS[@]}"; do
  session_name="ocd_rep50_${backend}_os"
  log_path="/tmp/${session_name}.log"
  if tmux has-session -t "$session_name" 2>/dev/null; then
    echo "Session already exists, skipping: ${session_name}"
    continue
  fi

  config_env=""
  output_env=""
  required_key_env=""
  case "$backend" in
    gemini)
      config_env="CONFIG_PATH=research/agent_eval/configs/frozen_config_gemini25pro_openrouter_one_shot.json"
      output_env="OUTPUT_DIR=research/results/ocd_gmae_rep50_v1_gemini_one_shot"
      required_key_env="REQUIRED_KEY=OPENROUTER_API_KEY"
      ;;
    grok)
      output_env="OUTPUT_DIR=research/results/ocd_gmae_rep50_v1_xai_grok4_one_shot"
      ;;
    gpt54)
      output_env="OUTPUT_DIR=research/results/ocd_gmae_rep50_v1_openai_gpt54_one_shot"
      ;;
    claude)
      output_env="OUTPUT_DIR=research/results/ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot"
      ;;
  esac

  tmux new-session -d -s "$session_name" \
    "bash -lc 'cd \"$ROOT_DIR\" && export MANIFEST_PATH=\"$MANIFEST_PATH\" $config_env $output_env $required_key_env && research/agent_eval/run_ocd_gmae_one_shot.sh \"$backend\" 2>&1 | tee \"$log_path\"'"
  echo "Started ${session_name} -> ${log_path}"
done
