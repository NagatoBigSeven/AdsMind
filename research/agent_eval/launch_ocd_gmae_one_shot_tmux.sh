#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required but not installed." >&2
  exit 1
fi

declare -a BACKENDS=("gemini" "grok" "gpt54" "claude")

for backend in "${BACKENDS[@]}"; do
  session_name="ocd_${backend}_os"
  log_path="/tmp/${session_name}.log"
  if tmux has-session -t "$session_name" 2>/dev/null; then
    echo "Session already exists, skipping: ${session_name}"
    continue
  fi
  tmux new-session -d -s "$session_name" \
    "bash -lc 'cd \"$ROOT_DIR\" && research/agent_eval/run_ocd_gmae_one_shot.sh \"$backend\" 2>&1 | tee \"$log_path\"'"
  echo "Started ${session_name} -> ${log_path}"
done
