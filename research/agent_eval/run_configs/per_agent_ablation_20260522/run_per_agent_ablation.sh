#!/usr/bin/env bash
# Per-agent ablation launcher: no_executor + no_validator on CMU20.
# Runs 4 backends in parallel, each goes through Phase A (no_executor, no MACE)
# then Phase B (no_validator, with MACE). DFT cases (01,02,03,04,09,10) are
# ordered first so they finish earliest for the morning audit.

set -uo pipefail
ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
PY="${PY:-${ROOT}/.venv/bin/python}"

cd "${ROOT}"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOGDIR="${ROOT}/research/results/run_logs/per_agent_ablation_${TIMESTAMP}"
mkdir -p "${LOGDIR}"
MASTER_LOG="${LOGDIR}/master.log"
: > "${MASTER_LOG}"

# DFT cases first, then the rest, so the 6 cases that have DFT reference values
# finish earliest.
CASES="01,02,03,04,09,10,05,06,07,08,11,12,13,14,15,16,17,18,19,20"
MANIFEST="datasets/cmu20/cmu20_manifest.csv"

run_backend() {
    local backend_dir=$1
    local config=$2
    local label=$3
    local logfile="${LOGDIR}/${label}.log"
    : > "${logfile}"

    {
        echo "=== ${label} START $(date -u +%H:%M:%SZ) ==="
        echo "[$(date -u +%H:%M:%SZ)] phase A no_executor"
        "${PY}" research/agent_eval/run_ablation.py \
            --manifest "${MANIFEST}" \
            --config "${config}" \
            --output "research/results/basic_experiments/cmu20/adsmind/${backend_dir}" \
            --cases "${CASES}" \
            --variants no_executor
        echo "[$(date -u +%H:%M:%SZ)] phase A DONE"

        echo "[$(date -u +%H:%M:%SZ)] phase B no_validator"
        "${PY}" research/agent_eval/run_ablation.py \
            --manifest "${MANIFEST}" \
            --config "${config}" \
            --output "research/results/basic_experiments/cmu20/adsmind/${backend_dir}" \
            --cases "${CASES}" \
            --variants no_validator
        echo "[$(date -u +%H:%M:%SZ)] phase B DONE"
        echo "=== ${label} END $(date -u +%H:%M:%SZ) ==="
    } >> "${logfile}" 2>&1
}

echo "[$(date -u +%H:%M:%SZ)] launching 4 backends in parallel" >> "${MASTER_LOG}"
echo "logdir=${LOGDIR}" >> "${MASTER_LOG}"

run_backend gpt54_mace_mp0_small            "research/agent_eval/configs/frozen_config_gpt54_mace_mp0_small.json"            gpt    &
PID_GPT=$!
run_backend claude_sonnet46_mace_mp0_small  "research/agent_eval/configs/frozen_config_claude_sonnet46_mace_mp0_small.json"  claude &
PID_CLAUDE=$!
run_backend gemini25pro_mace_mp0_small      "research/agent_eval/configs/frozen_config_gemini25pro_mace_mp0_small.json"      gemini &
PID_GEMINI=$!
run_backend grok4_mace_mp0_small            "research/agent_eval/configs/frozen_config_grok4_mace_mp0_small.json"            grok   &
PID_GROK=$!

echo "pids: gpt=${PID_GPT} claude=${PID_CLAUDE} gemini=${PID_GEMINI} grok=${PID_GROK}" >> "${MASTER_LOG}"

wait
echo "[$(date -u +%H:%M:%SZ)] ALL BACKENDS COMPLETE" >> "${MASTER_LOG}"
