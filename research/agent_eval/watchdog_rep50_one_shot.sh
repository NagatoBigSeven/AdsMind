#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MANIFEST_PATH="${MANIFEST_PATH:-research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv}"
LOG_PATH="${LOG_PATH:-/tmp/ocd_rep50_guard.log}"
POLL_SECONDS="${POLL_SECONDS:-300}"

declare -A OUTPUT_DIRS=(
  [gemini]="research/results/ocd_gmae_rep50_v1_gemini_one_shot"
  [grok]="research/results/ocd_gmae_rep50_v1_xai_grok4_one_shot"
  [gpt54]="research/results/ocd_gmae_rep50_v1_openai_gpt54_one_shot"
  [claude]="research/results/ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot"
)

declare -A CONFIG_PATHS=(
  [gemini]="research/agent_eval/configs/frozen_config_gemini25pro_openrouter_one_shot.json"
  [grok]=""
  [gpt54]=""
  [claude]=""
)

declare -A REQUIRED_KEYS=(
  [gemini]="OPENROUTER_API_KEY"
  [grok]="XAI_API_KEY"
  [gpt54]="OPENAI_API_KEY"
  [claude]="ANTHROPIC_API_KEY"
)

declare -A SESSION_NAMES=(
  [gemini]="ocd_rep50_gemini_os"
  [grok]="ocd_rep50_grok_os"
  [gpt54]="ocd_rep50_gpt54_os"
  [claude]="ocd_rep50_claude_os"
)

declare -A SESSION_LOGS=(
  [gemini]="/tmp/ocd_rep50_gemini_os.log"
  [grok]="/tmp/ocd_rep50_grok_os.log"
  [gpt54]="/tmp/ocd_rep50_gpt54_os.log"
  [claude]="/tmp/ocd_rep50_claude_os.log"
)

export_tmux_env() {
  for key in OPENROUTER_API_KEY AIHUBMIX_API_KEY XAI_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY; do
    if [[ -n "${!key:-}" ]]; then
      tmux set-environment -g "$key" "${!key}"
    fi
  done
}

start_backend_if_needed() {
  local backend="$1"
  local session_name="${SESSION_NAMES[$backend]}"
  local summary_path="${OUTPUT_DIRS[$backend]}/summary.csv"
  local log_path="${SESSION_LOGS[$backend]}"

  if [[ -f "$summary_path" ]]; then
    return 0
  fi
  if tmux has-session -t "$session_name" 2>/dev/null; then
    return 0
  fi

  local config_export=""
  local required_key_export=""
  if [[ -n "${CONFIG_PATHS[$backend]}" ]]; then
    config_export="CONFIG_PATH=${CONFIG_PATHS[$backend]}"
  fi
  if [[ -n "${REQUIRED_KEYS[$backend]}" ]]; then
    required_key_export="REQUIRED_KEY=${REQUIRED_KEYS[$backend]}"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] restarting $backend into $session_name" >> "$LOG_PATH"
  tmux new-session -d -s "$session_name" \
    "bash -lc 'cd \"$ROOT_DIR\" && export MANIFEST_PATH=\"$MANIFEST_PATH\" OUTPUT_DIR=\"${OUTPUT_DIRS[$backend]}\" $config_export $required_key_export && research/agent_eval/run_ocd_gmae_one_shot.sh \"$backend\" --skip-existing 2>&1 | tee \"$log_path\"'"
}

ensure_rank_wait() {
  if tmux has-session -t ocd_rep50_rank_wait 2>/dev/null; then
    return 0
  fi
  if [[ -f research/results/ocd_gmae_rep50_one_shot_range_ranking.csv ]]; then
    return 0
  fi
  tmux new-session -d -s ocd_rep50_rank_wait \
    "bash -lc 'cd \"$ROOT_DIR\" && while [ ! -f research/results/ocd_gmae_rep50_v1_gemini_one_shot/summary.csv ] || [ ! -f research/results/ocd_gmae_rep50_v1_xai_grok4_one_shot/summary.csv ] || [ ! -f research/results/ocd_gmae_rep50_v1_openai_gpt54_one_shot/summary.csv ] || [ ! -f research/results/ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot/summary.csv ]; do sleep 300; done && python -m research.agent_eval.rank_one_shot_ranges --summary gemini=research/results/ocd_gmae_rep50_v1_gemini_one_shot/summary.csv --summary grok=research/results/ocd_gmae_rep50_v1_xai_grok4_one_shot/summary.csv --summary gpt54=research/results/ocd_gmae_rep50_v1_openai_gpt54_one_shot/summary.csv --summary claude=research/results/ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot/summary.csv --output-csv research/results/ocd_gmae_rep50_one_shot_range_ranking.csv --output-json research/results/ocd_gmae_rep50_one_shot_range_ranking.json --require-success > /tmp/ocd_rep50_rank_wait.log 2>&1'"
}

ensure_eval_wait() {
  if tmux has-session -t ocd_rep50_eval_wait 2>/dev/null; then
    return 0
  fi
  if [[ -f research/results/ocd_gmae_rep50_ground_truth_eval.csv ]]; then
    return 0
  fi
  tmux new-session -d -s ocd_rep50_eval_wait \
    "bash -lc 'cd \"$ROOT_DIR\" && while [ ! -f research/results/ocd_gmae_rep50_v1_gemini_one_shot/summary.csv ] || [ ! -f research/results/ocd_gmae_rep50_v1_xai_grok4_one_shot/summary.csv ] || [ ! -f research/results/ocd_gmae_rep50_v1_openai_gpt54_one_shot/summary.csv ] || [ ! -f research/results/ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot/summary.csv ]; do sleep 300; done && python -m research.agent_eval.evaluate_ocd_gmae_ground_truth --manifest research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv --summary gemini=research/results/ocd_gmae_rep50_v1_gemini_one_shot/summary.csv --summary grok=research/results/ocd_gmae_rep50_v1_xai_grok4_one_shot/summary.csv --summary gpt54=research/results/ocd_gmae_rep50_v1_openai_gpt54_one_shot/summary.csv --summary claude=research/results/ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot/summary.csv --output-csv research/results/ocd_gmae_rep50_ground_truth_eval.csv --output-json research/results/ocd_gmae_rep50_ground_truth_eval.json > /tmp/ocd_rep50_eval_wait.log 2>&1'"
}

while true; do
  export_tmux_env
  for backend in gemini grok gpt54 claude; do
    start_backend_if_needed "$backend"
  done
  ensure_rank_wait
  ensure_eval_wait
  sleep "$POLL_SECONDS"
done
