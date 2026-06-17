"""Run OCD62 overlap12 RUN4/RUN5 with backend-parallel streams."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.common import ABLATED_VARIANTS, load_frozen_config, load_manifest_map
from research.agent_eval.run_case import execute_case

BACKENDS = ("gemini", "grok4", "openai_gpt54", "anthropic_sonnet46")
VARIANTS = ("full", "no_slip", "no_forbid", "no_termination", "single_shot")
CASES = tuple(f"{idx:03d}" for idx in range(1, 13))
RUN_IDS = (4, 5)

CONFIGS = {
    "gemini": ROOT / "research/agent_eval/configs/ocd62_run3_openrouter/frozen_config_ocd62_run3_openrouter_gemini.json",
    "grok4": ROOT / "research/agent_eval/configs/ocd62_run3_openrouter/frozen_config_ocd62_run3_openrouter_grok4.json",
    "openai_gpt54": ROOT / "research/agent_eval/configs/ocd62_run3/frozen_config_ocd62_run3_openai_gpt54.json",
    "anthropic_sonnet46": ROOT / "research/agent_eval/configs/ocd62_run3/frozen_config_ocd62_run3_anthropic_sonnet46.json",
}
KEY_PLANS = {
    "gemini": (("openrouter-primary", "OPENROUTER_API_KEY_PRIMARY"), ("openrouter-secondary", "OPENROUTER_API_KEY_SECONDARY")),
    "grok4": (("openrouter-primary", "OPENROUTER_API_KEY_PRIMARY"), ("openrouter-secondary", "OPENROUTER_API_KEY_SECONDARY")),
    "openai_gpt54": (("openai-native", "OPENAI_API_KEY"),),
    "anthropic_sonnet46": (("anthropic-native", "ANTHROPIC_API_KEY"),),
}

SUMMARY_FIELDS = [
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

EXTERNAL_MARKERS = (
    "service temporarily unavailable",
    "temporarily unavailable",
    "capacity",
    "code': 502",
    '"code": 502',
    " 502",
    " 503",
    " 504",
    "rate limit",
    "429",
    "402",
    "more credits",
    "credits",
    "can only afford",
    "billing",
    "payment",
    "insufficient",
    "quota",
    "key limit exceeded",
    "limit exceeded",
    "internal server error",
    "code': 500",
    '"code": 500',
    " 500",
    "overloaded",
    "timeout",
    "timed out",
    "connection",
    "remote protocol",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def output_root(run_id: int, backend: str) -> Path:
    return ROOT / f"research/results/canonical_raw/ocd62_overlap12_run{run_id}_{backend}_ablation"


def result_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "error", "error": "invalid result.json"}


def is_external_failure(payload: dict[str, object]) -> bool:
    if payload.get("status") == "success":
        return False
    text = json.dumps(payload, ensure_ascii=False).lower()
    return any(marker in text for marker in EXTERNAL_MARKERS)


def is_complete(run_id: int, backend: str, variant: str, case_id: str) -> bool:
    payload = result_payload(output_root(run_id, backend) / variant / case_id / "result.json")
    return payload.get("status") == "success" or (payload.get("status") == "failed" and not is_external_failure(payload))


def summarize(run_id: int, backend: str) -> None:
    root = output_root(run_id, backend)
    rows: list[dict[str, object]] = []
    full_energy_by_case: dict[str, float] = {}
    for case_id in CASES:
        payload = result_payload(root / "full" / case_id / "result.json")
        e = payload.get("best_energy_eV")
        if isinstance(e, (int, float)):
            full_energy_by_case[case_id] = float(e)
    for variant in VARIANTS:
        for case_id in CASES:
            payload = result_payload(root / variant / case_id / "result.json")
            e = payload.get("best_energy_eV")
            iters = payload.get("iteration_count", 0) or 0
            calc_fail = payload.get("calc_failure_count", 0) or 0
            delta = None
            if case_id in full_energy_by_case and isinstance(e, (int, float)):
                delta = float(e) - full_energy_by_case[case_id]
            rows.append(
                {
                    "case_id": case_id,
                    "variant": variant,
                    "best_energy": e,
                    "delta_vs_full": delta,
                    "iterations": iters,
                    "wasted_iterations": calc_fail,
                    "waste_ratio": (calc_fail / iters) if iters else 0,
                    "success": payload.get("status") == "success",
                    "slip_count": payload.get("chemical_slip_count", 0),
                    "dissociation_count": payload.get("dissociation_count", 0),
                    "tokens_used": (payload.get("total_input_tokens", 0) or 0) + (payload.get("total_output_tokens", 0) or 0),
                }
            )
    root.mkdir(parents=True, exist_ok=True)
    with (root / "ablation_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (root / "ablation_stats.json").write_text(
        json.dumps({"backend": backend, "run_id": run_id, "timestamp": utc_now(), "note": "RUN4/RUN5 summary rebuilt from result.json files."}, indent=2) + "\n",
        encoding="utf-8",
    )


def run_task(*, run_id: int, backend: str, variant: str, case_id: str, manifest: dict[str, dict[str, str]], frozen: dict[str, object], log) -> bool:
    if is_complete(run_id, backend, variant, case_id):
        log.write(f"[{utc_now()}] SKIP run={run_id} backend={backend} variant={variant} case={case_id} complete\n")
        log.flush()
        return True
    root = output_root(run_id, backend)
    key_plan = KEY_PLANS[backend]
    attempts: list[tuple[str, str]] = []
    for slot, env_var in key_plan:
        attempts.append((slot, env_var))
    if len(attempts) == 1:
        attempts = attempts * 3
    last_payload: dict[str, object] = {}
    for attempt_idx, (slot, env_var) in enumerate(attempts, start=1):
        key = os.environ.get(env_var, "")
        if not key:
            log.write(f"[{utc_now()}] MISSING_KEY run={run_id} backend={backend} env={env_var}\n")
            log.flush()
            return False
        log.write(f"[{utc_now()}] RUN run={run_id} backend={backend} variant={variant} case={case_id} key_slot={slot} attempt={attempt_idx}\n")
        log.flush()
        try:
            run = execute_case(
                case_row=manifest[case_id],
                frozen_config=frozen,
                output_root=root / variant,
                runtime_overrides=ABLATED_VARIANTS[variant],
                explicit_api_key=key,
                dry_run=False,
                repo_root=ROOT,
            )
            last_payload = run.result
            status = last_payload.get("status")
            external = is_external_failure(last_payload)
            log.write(f"[{utc_now()}] END run={run_id} backend={backend} variant={variant} case={case_id} status={status} external={external}\n")
            log.flush()
            summarize(run_id, backend)
            if status == "success" or (status == "failed" and not external):
                return True
            if len(key_plan) > 1 and slot == "openrouter-primary" and external:
                continue
            if not external:
                return False
        except Exception as exc:
            msg = str(exc).replace("\n", " ")[:300]
            log.write(f"[{utc_now()}] EXCEPTION run={run_id} backend={backend} variant={variant} case={case_id} key_slot={slot} msg={msg}\n")
            log.write(traceback.format_exc()[-2000:] + "\n")
            log.flush()
        time.sleep(20)
    summarize(run_id, backend)
    return False


def parse_int_filter(raw: str, *, choices: tuple[int, ...]) -> tuple[int, ...]:
    if not raw:
        return choices
    requested = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    invalid = sorted(set(requested) - set(choices))
    if invalid:
        raise ValueError(f"Invalid run ids: {invalid}")
    return requested


def parse_str_filter(raw: str, *, choices: tuple[str, ...], label: str) -> tuple[str, ...]:
    if not raw:
        return choices
    requested = tuple(part.strip() for part in raw.split(",") if part.strip())
    invalid = sorted(set(requested) - set(choices))
    if invalid:
        raise ValueError(f"Invalid {label}: {invalid}")
    return requested


def backend_stream(
    backend: str,
    log_dir: Path,
    *,
    run_ids: tuple[int, ...] = RUN_IDS,
    variants: tuple[str, ...] = VARIANTS,
    cases: tuple[str, ...] = CASES,
    config_path: Path | None = None,
) -> int:
    manifest = load_manifest_map(str(ROOT / "datasets/ocd62_overlap12/manifest.csv"))
    frozen = load_frozen_config(str(config_path or CONFIGS[backend]))
    log_path = log_dir / f"{backend}.log"
    failures: list[str] = []
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== backend stream started backend={backend} at {utc_now()} ===\n")
        log.flush()
        for run_id in run_ids:
            for variant in variants:
                for case_id in cases:
                    ok = run_task(run_id=run_id, backend=backend, variant=variant, case_id=case_id, manifest=manifest, frozen=frozen, log=log)
                    if not ok:
                        failures.append(f"run{run_id}/{backend}/{variant}/{case_id}")
            summarize(run_id, backend)
        log.write(f"=== backend stream finished backend={backend} failures={failures} at {utc_now()} ===\n")
        log.flush()
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", required=True, choices=BACKENDS)
    parser.add_argument("--log-dir", default="research/results/run_logs/ocd62_run45")
    parser.add_argument("--runs", default="", help="Comma-separated run ids to process, default: all")
    parser.add_argument("--variants", default="", help="Comma-separated variants to process, default: all")
    parser.add_argument("--cases", default="", help="Comma-separated case ids to process, default: all")
    parser.add_argument("--config", default="", help="Optional frozen config override for the selected backend")
    args = parser.parse_args(argv)
    run_ids = parse_int_filter(args.runs, choices=RUN_IDS)
    variants = parse_str_filter(args.variants, choices=VARIANTS, label="variants")
    cases = parse_str_filter(args.cases, choices=CASES, label="cases")
    config_path = (ROOT / args.config).resolve() if args.config else None
    return backend_stream(
        args.backend,
        (ROOT / args.log_dir).resolve(),
        run_ids=run_ids,
        variants=variants,
        cases=cases,
        config_path=config_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
