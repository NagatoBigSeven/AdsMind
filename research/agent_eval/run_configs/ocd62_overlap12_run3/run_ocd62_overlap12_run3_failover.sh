#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
PY="${PY:-${ROOT}/.venv/bin/python}"

cd "${ROOT}"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

exec "${PY}" research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.py "$@"
