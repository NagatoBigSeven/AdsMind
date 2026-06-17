"""Run OCD62 overlap12 RUN3 as resumable tasks with backend-specific keys."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import BACKEND_KEYS, backend_identity, backend_result_dir, summary_metadata

BACKENDS = BACKEND_KEYS
VARIANTS = ("full", "no_slip", "no_forbid", "no_termination", "one_shot")
CASES = tuple(f"{idx:03d}" for idx in range(1, 13))
OPENROUTER_BACKENDS = {"gemini", "grok"}
CONFIG_BACKEND = {
    "gpt": "gpt54_mace_mp0_small",
    "claude": "claude_sonnet46_mace_mp0_small",
    "gemini": "gemini25pro_mace_mp0_small",
    "grok": "grok4_mace_mp0_small",
}
EXPECTED_PROTOCOL = {
    "gemini": {
        "llm_backend": "openrouter",
        "llm_model": {"gemini-2.5-pro", "google/gemini-2.5-pro"},
        "llm_base_url": "https://openrouter.ai/api/v1",
        "llm_api_key_env_var": "OPENROUTER_API_KEY",
    },
    "grok": {
        "llm_backend": "openrouter",
        "llm_model": {"grok-4", "x-ai/grok-4"},
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
FAILOVER_MARKERS = (
    "401",
    "402",
    "403",
    "429",
    "api key",
    "authentication",
    "authorization",
    "auth",
    "credit",
    "insufficient",
    "invalid x-api-key",
    "key",
    "limit",
    "payment",
    "quota",
    "rate",
    "unauthorized",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_key(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    path = os.environ.get(f"{name}_FILE")
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8").strip()
    return None


def delete_key_file(name: str) -> None:
    if os.environ.get("OPENROUTER_DELETE_KEY_FILES") != "1":
        return
    path = os.environ.get(f"{name}_FILE")
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def required_key_names(backends: tuple[str, ...]) -> tuple[str, ...]:
    names: list[str] = []
    if any(backend in OPENROUTER_BACKENDS for backend in backends):
        names.extend(["OPENROUTER_API_KEY_PRIMARY", "OPENROUTER_API_KEY_SECONDARY"])
    if "gpt" in backends:
        names.append("OPENAI_API_KEY")
    if "claude" in backends:
        names.append("ANTHROPIC_API_KEY")
    return tuple(dict.fromkeys(names))


def load_runtime_keys(backends: tuple[str, ...]) -> dict[str, str]:
    keys = {name: read_key(name) for name in required_key_names(backends)}
    missing = [name for name, value in keys.items() if not value]
    if missing:
        raise SystemExit(
            "Missing required API keys or *_FILE variants: " + ", ".join(missing)
        )
    for name in keys:
        delete_key_file(name)
    return {name: value for name, value in keys.items() if value is not None}


def config_for_backend(
    backend: str,
    *,
    config_dir: Path,
) -> Path:
    config_backend = CONFIG_BACKEND[backend]
    return config_dir / f"frozen_config_ocd62_overlap12_run3_{config_backend}.json"


def key_plan_for_backend(backend: str, keys: dict[str, str]) -> tuple[tuple[str, str, str], ...]:
    """Return (slot label, env var, key) entries for one backend."""
    if backend in OPENROUTER_BACKENDS:
        return (
            ("openrouter-primary", "OPENROUTER_API_KEY", keys["OPENROUTER_API_KEY_PRIMARY"]),
            ("openrouter-secondary", "OPENROUTER_API_KEY", keys["OPENROUTER_API_KEY_SECONDARY"]),
        )
    if backend == "gpt":
        return (("openai-native", "OPENAI_API_KEY", keys["OPENAI_API_KEY"]),)
    if backend == "claude":
        return (("anthropic-native", "ANTHROPIC_API_KEY", keys["ANTHROPIC_API_KEY"]),)
    raise ValueError(f"Unknown backend: {backend}")


def protocol_matches(backend: str, case_dir: Path) -> bool:
    config_path = case_dir / "config.json"
    if not config_path.exists():
        return False
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    frozen = payload.get("frozen_config") or {}
    expected = EXPECTED_PROTOCOL[backend]
    for key, value in expected.items():
        actual = frozen.get(key)
        if isinstance(value, set):
            if actual not in value:
                return False
        elif actual != value:
            return False
    return True


def backup_protocol_mismatch(backend: str, case_dir: Path) -> None:
    if not case_dir.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = case_dir.with_name(f"{case_dir.name}_protocol_mismatch_{backend}_{stamp}")
    counter = 1
    while backup.exists():
        backup = case_dir.with_name(f"{case_dir.name}_protocol_mismatch_{backend}_{stamp}_{counter}")
        counter += 1
    case_dir.rename(backup)


def success_result(output_root: Path, backend: str, variant: str, case_id: str, *, repair: bool = False) -> bool:
    case_dir = output_root / variant / case_id
    result_path = output_root / variant / case_id / "result.json"
    if not result_path.exists():
        return False
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if payload.get("status") != "success":
        return False
    if protocol_matches(backend, case_dir):
        return True
    if repair:
        backup_protocol_mismatch(backend, case_dir)
    return False


def summarize_backend(output_root: Path, backend: str, variants: tuple[str, ...], cases: tuple[str, ...]) -> None:
    rows: list[dict[str, object]] = []
    full_energy_by_case: dict[str, float] = {}
    metadata = summary_metadata(backend_identity(backend, run_name="run3"))
    for variant in variants:
        for case_id in cases:
            result_path = output_root / variant / case_id / "result.json"
            result: dict[str, object] = {}
            if result_path.exists():
                try:
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    result = {"status": "error", "error": "Invalid result.json"}
            best_energy = result.get("best_energy_eV")
            if variant == "full" and isinstance(best_energy, (int, float)):
                full_energy_by_case[case_id] = float(best_energy)
            delta = None
            if case_id in full_energy_by_case and isinstance(best_energy, (int, float)):
                delta = float(best_energy) - full_energy_by_case[case_id]
            rows.append(
                {
                    **metadata,
                    "case_id": case_id,
                    "variant": variant,
                    "best_energy": best_energy,
                    "delta_vs_full": delta,
                    "iterations": result.get("iteration_count", 0),
                    "wasted_iterations": result.get("calc_failure_count", 0),
                    "waste_ratio": (
                        (result.get("calc_failure_count", 0) / result.get("iteration_count", 1))
                        if result.get("iteration_count", 0)
                        else 0
                    ),
                    "success": result.get("status") == "success",
                    "slip_count": result.get("chemical_slip_count", 0),
                    "dissociation_count": result.get("dissociation_count", 0),
                    "tokens_used": result.get("total_input_tokens", 0) + result.get("total_output_tokens", 0),
                }
            )

    output_root.mkdir(parents=True, exist_ok=True)
    summary_path = output_root / "all_variants_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "backend_key",
            "backend",
            "llm_model",
            "force_field",
            "calculator_backend",
            "force_field_model",
            "force_field_size",
            "case_id",
            "variant",
            "best_energy",
            "delta_vs_full",
            "iterations",
            "wasted_iterations",
            "waste_ratio",
            "success",
            "slip_count",
            "dissociation_count",
            "tokens_used",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    stats_path = output_root / "all_variants_stats.json"
    stats_path.write_text(
        json.dumps(
            {
                "friedman": None,
                "pairwise": {},
                "bh_fdr": {},
                "note": (
                    "Summary assembled by run_ocd62_overlap12_run3_failover.py. "
                    "Use research.agent_eval.run_ablation for full statistical tests if needed."
                ),
                "backend": backend,
                "timestamp": utc_now(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_one(
    *,
    py: str,
    manifest: Path,
    config: Path,
    output_root: Path,
    case_id: str,
    variant: str,
    key: str,
    key_slot: str,
    key_env_var: str,
    log_path: Path,
) -> tuple[int, str]:
    env = os.environ.copy()
    env[key_env_var] = key
    cmd = [
        py,
        "-m",
        "research.agent_eval.run_ablation",
        "--manifest",
        str(manifest),
        "--config",
        str(config),
        "--output",
        str(output_root),
        "--cases",
        case_id,
        "--variants",
        variant,
    ]
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"[{utc_now()}] START case={case_id} variant={variant} key_slot={key_slot}\n")
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        log.write(f"[{utc_now()}] END case={case_id} variant={variant} key_slot={key_slot} rc={proc.returncode}\n")
    try:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-12000:]
    except OSError:
        tail = ""
    return proc.returncode, tail


def should_switch_key(returncode: int, text: str) -> bool:
    if returncode == 0:
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in FAILOVER_MARKERS)


def parse_csv_tuple(value: str, allowed: tuple[str, ...], label: str) -> tuple[str, ...]:
    if value == "all":
        return allowed
    selected = tuple(item.strip() for item in value.split(",") if item.strip())
    unknown = [item for item in selected if item not in allowed]
    if unknown:
        raise ValueError(f"Unknown {label}: {', '.join(unknown)}")
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="datasets/ocd62_overlap12/ocd62_overlap12_manifest.csv")
    parser.add_argument("--config-dir", default="research/agent_eval/configs/ocd62_overlap12_run3")
    parser.add_argument(
        "--output-base",
        default="research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3",
    )
    parser.add_argument("--log-dir", default="research/agent_eval/run_configs/ocd62_overlap12_run3/logs")
    parser.add_argument("--backends", default="all")
    parser.add_argument("--variants", default="all")
    parser.add_argument("--cases", default="all")
    parser.add_argument("--sleep-after-failure-sec", type=int, default=20)
    parser.add_argument("--max-attempts-per-key", type=int, default=1)
    args = parser.parse_args(argv)

    py = os.environ.get("PY", str(ROOT / ".venv/bin/python"))
    manifest = (ROOT / args.manifest).resolve()
    config_dir = (ROOT / args.config_dir).resolve()
    output_base = (ROOT / args.output_base).resolve()
    log_dir = (ROOT / args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    backends = parse_csv_tuple(args.backends, BACKENDS, "backend")
    variants = parse_csv_tuple(args.variants, VARIANTS, "variant")
    cases = parse_csv_tuple(args.cases, CASES, "case")
    keys = load_runtime_keys(backends)

    failures: list[str] = []
    for backend in backends:
        config = config_for_backend(
            backend,
            config_dir=config_dir,
        )
        output_root = output_base / backend_result_dir(backend, run_name="run3")
        if not config.exists():
            raise FileNotFoundError(config)
        for variant in variants:
            for case_id in cases:
                if success_result(output_root, backend, variant, case_id, repair=True):
                    print(f"[{utc_now()}] SKIP backend={backend} variant={variant} case={case_id} already_success")
                    continue

                task_log = log_dir / f"{backend}_{variant}_{case_id}.log"
                completed = False
                key_plan = key_plan_for_backend(backend, keys)
                for key_index, (slot, key_env_var, key) in enumerate(key_plan):
                    for attempt in range(1, args.max_attempts_per_key + 1):
                        print(
                            f"[{utc_now()}] RUN backend={backend} variant={variant} "
                            f"case={case_id} key_slot={slot} attempt={attempt}",
                            flush=True,
                        )
                        rc, tail = run_one(
                            py=py,
                            manifest=manifest,
                            config=config,
                            output_root=output_root,
                            case_id=case_id,
                            variant=variant,
                            key=key,
                            key_slot=slot,
                            key_env_var=key_env_var,
                            log_path=task_log,
                        )
                        if rc == 0 and success_result(output_root, backend, variant, case_id):
                            completed = True
                            break
                        if len(key_plan) > 1 and key_index == 0 and should_switch_key(rc, tail):
                            print(
                                f"[{utc_now()}] FAILOVER backend={backend} variant={variant} "
                                f"case={case_id} primary_to_secondary",
                                flush=True,
                            )
                            break
                        if args.sleep_after_failure_sec:
                            time.sleep(args.sleep_after_failure_sec)
                    if completed:
                        break
                if not completed:
                    failures.append(f"{backend}/{variant}/{case_id}")
                summarize_backend(output_root, backend, variants, cases)

    if failures:
        print("FAILED TASKS:")
        for item in failures:
            print(f"- {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
