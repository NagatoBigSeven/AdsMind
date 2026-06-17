#!/usr/bin/env bash
# Standalone Grok-4.3 launcher for the per-agent ablation.
# Created 2026-05-22 after OpenRouter deprecated Grok-4.
# Runs no_executor then no_validator on the full CMU20 20-case set.

set -uo pipefail
ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
PY="${PY:-${ROOT}/.venv/bin/python}"

cd "${ROOT}"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOGDIR="${ROOT}/research/results/run_logs/per_agent_ablation_grok43_${TIMESTAMP}"
mkdir -p "${LOGDIR}"
LOGFILE="${LOGDIR}/grok43.log"
: > "${LOGFILE}"

CASES="01,02,03,04,09,10,05,06,07,08,11,12,13,14,15,16,17,18,19,20"
MANIFEST="datasets/cmu20/cmu20_manifest.csv"
CONFIG="research/agent_eval/configs/frozen_config_grok43_mace_mp0_small.json"
OUTPUT="research/results/basic_experiments/cmu20/adsmind/grok4_mace_mp0_small"

{
    echo "=== grok-4.3 START $(date -u +%H:%M:%SZ) ==="
    echo "[$(date -u +%H:%M:%SZ)] phase A no_executor"
    "${PY}" research/agent_eval/run_ablation.py \
        --manifest "${MANIFEST}" \
        --config "${CONFIG}" \
        --output "${OUTPUT}" \
        --cases "${CASES}" \
        --variants no_executor
    echo "[$(date -u +%H:%M:%SZ)] phase A DONE"

    echo "[$(date -u +%H:%M:%SZ)] phase B no_validator"
    "${PY}" research/agent_eval/run_ablation.py \
        --manifest "${MANIFEST}" \
        --config "${CONFIG}" \
        --output "${OUTPUT}" \
        --cases "${CASES}" \
        --variants no_validator
    echo "[$(date -u +%H:%M:%SZ)] phase B DONE"
    echo "=== grok-4.3 END $(date -u +%H:%M:%SZ) ==="
} >> "${LOGFILE}" 2>&1
