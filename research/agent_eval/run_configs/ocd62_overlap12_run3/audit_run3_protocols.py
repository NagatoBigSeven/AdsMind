"""Audit RUN3 result configs for expected backend transport provenance."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import BACKEND_KEYS, backend_result_dir

BACKENDS = BACKEND_KEYS
VARIANTS = ("full", "no_slip", "no_forbid", "no_termination", "one_shot")
CASES = tuple(f"{idx:03d}" for idx in range(1, 13))
EXPECTED = {
    "gemini": {
        "llm_backend": "openrouter",
        "llm_model": "google/gemini-2.5-pro",
        "llm_base_url": "https://openrouter.ai/api/v1",
        "llm_api_key_env_var": "OPENROUTER_API_KEY",
    },
    "grok": {
        "llm_backend": "openrouter",
        "llm_model": "x-ai/grok-4",
        "llm_base_url": "https://openrouter.ai/api/v1",
        "llm_api_key_env_var": "OPENROUTER_API_KEY",
    },
    "gpt": {
        "llm_model": "gpt-5.4-2026-03-05",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_api_key_env_var": "OPENAI_API_KEY",
    },
    "claude": {
        "llm_backend": "anthropic",
        "llm_model": "claude-sonnet-4-6",
        "llm_base_url": "https://api.anthropic.com/v1/",
        "llm_api_key_env_var": "ANTHROPIC_API_KEY",
    },
}


def case_dir(backend: str, variant: str, case_id: str) -> Path:
    return (
        ROOT
        / "research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3"
        / backend_result_dir(backend, run_name="run3")
        / variant
        / case_id
    )


def status_for(backend: str, variant: str, case_id: str) -> tuple[str, str]:
    directory = case_dir(backend, variant, case_id)
    result_path = directory / "result.json"
    config_path = directory / "config.json"
    if not result_path.exists():
        return "MISSING", ""
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "BAD_RESULT_JSON", ""
    if result.get("status") != "success":
        return "NOT_SUCCESS", str(result.get("status"))
    if not config_path.exists():
        return "MISSING_CONFIG", ""
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "BAD_CONFIG_JSON", ""
    frozen = config.get("frozen_config") or {}
    mismatches = []
    for key, expected in EXPECTED[backend].items():
        actual = frozen.get(key)
        if actual != expected:
            mismatches.append(f"{key}: expected={expected!r} actual={actual!r}")
    if mismatches:
        return "PROTOCOL_MISMATCH", "; ".join(mismatches)
    return "OK", frozen.get("llm_backend", "")


def main() -> int:
    counts: dict[str, int] = {}
    problems: list[str] = []
    for backend in BACKENDS:
        for variant in VARIANTS:
            for case_id in CASES:
                status, detail = status_for(backend, variant, case_id)
                counts[status] = counts.get(status, 0) + 1
                if status not in {"OK", "MISSING"}:
                    problems.append(f"{backend}/{variant}/{case_id}: {status} {detail}")
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    if problems:
        print("PROBLEMS:")
        for item in problems:
            print(item)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
