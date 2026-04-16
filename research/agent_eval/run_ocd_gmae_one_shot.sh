#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <gemini|grok|gpt54|claude> [extra run_batch args...]" >&2
  exit 1
fi

BACKEND="$1"
shift

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

MANIFEST_PATH="${MANIFEST_PATH:-research/agent_eval/manifests/ocd_gmae_manifest.csv}"

case "$BACKEND" in
  gemini)
    DEFAULT_CONFIG="research/agent_eval/configs/frozen_config_gemini25pro_one_shot.json"
    DEFAULT_OUTPUT="research/results/ocd_gmae_v1_gemini_one_shot"
    DEFAULT_REQUIRED_KEY="AIHUBMIX_API_KEY"
    ;;
  grok)
    DEFAULT_CONFIG="research/agent_eval/configs/frozen_config_xai_grok4_one_shot.json"
    DEFAULT_OUTPUT="research/results/ocd_gmae_v1_xai_grok4_one_shot"
    DEFAULT_REQUIRED_KEY="XAI_API_KEY"
    ;;
  gpt54)
    DEFAULT_CONFIG="research/agent_eval/configs/frozen_config_openai_gpt54_one_shot.json"
    DEFAULT_OUTPUT="research/results/ocd_gmae_v1_openai_gpt54_one_shot"
    DEFAULT_REQUIRED_KEY="OPENAI_API_KEY"
    ;;
  claude)
    DEFAULT_CONFIG="research/agent_eval/configs/frozen_config_anthropic_sonnet46_one_shot.json"
    DEFAULT_OUTPUT="research/results/ocd_gmae_v1_anthropic_sonnet46_one_shot"
    DEFAULT_REQUIRED_KEY="ANTHROPIC_API_KEY"
    ;;
  *)
    echo "Unknown backend: ${BACKEND}" >&2
    exit 1
    ;;
esac

CONFIG_PATH="${CONFIG_PATH:-$DEFAULT_CONFIG}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"
REQUIRED_KEY="${REQUIRED_KEY:-$DEFAULT_REQUIRED_KEY}"

REQUIRES_KEY=1
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    REQUIRES_KEY=0
    break
  fi
done

if [[ "$REQUIRES_KEY" -eq 1 && -z "${!REQUIRED_KEY:-}" ]]; then
  echo "Missing required environment variable: ${REQUIRED_KEY}" >&2
  exit 1
fi

exec "$PYTHON_BIN" -m research.agent_eval.run_batch \
  --manifest "$MANIFEST_PATH" \
  --config "$CONFIG_PATH" \
  --output "$OUTPUT_DIR" \
  "$@"
