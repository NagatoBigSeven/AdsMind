#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_PATH="${LOG_PATH:-/tmp/ocd_gem_recover_supervisor.log}"
PID_PATH="${PID_PATH:-/tmp/ocd_gem_recover_supervisor.pid}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib}"
mkdir -p "$MPLCONFIGDIR"

if [[ -f "$PID_PATH" ]]; then
  old_pid="$(cat "$PID_PATH" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "watchdog already running with pid $old_pid"
    exit 0
  fi
fi

echo "$$" > "$PID_PATH"
trap 'rm -f "$PID_PATH"' EXIT

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

while true; do
  timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[$timestamp] starting gemini recovery robust" >> "$LOG_PATH"
  set +e
  MPLCONFIGDIR="$MPLCONFIGDIR" "$PYTHON_BIN" -m research.agent_eval.recover_ocd_gmae_gemini_robust >> "$LOG_PATH" 2>&1
  rc=$?
  set -e
  timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[$timestamp] gemini recovery robust exited rc=$rc" >> "$LOG_PATH"

  failed_cells_csv="research/results/ocd_gmae_gemini_ablation_failed_cells.csv"
  if [[ -f "$failed_cells_csv" ]]; then
    remaining="$(python - <<'PY'
import csv
from pathlib import Path
p = Path("research/results/ocd_gmae_gemini_ablation_failed_cells.csv")
if not p.exists():
    print("unknown")
else:
    with p.open() as f:
        rows = list(csv.DictReader(f))
    print(len(rows))
PY
)"
    echo "[$timestamp] remaining_failed_cells=$remaining" >> "$LOG_PATH"
    if [[ "$remaining" == "0" ]]; then
      echo "[$timestamp] recovery complete, watchdog exiting" >> "$LOG_PATH"
      exit 0
    fi
  fi

  sleep 60
done
