#!/usr/bin/env python3
"""Grok-4 outlier seed sweep follow-up (advisor audit 2026-05-09).

Reseeds Grok-4-only outliers that survived the run5 rerun:
  - CMU20 case 20 grok one_shot   (continuation of seed_43..47 sweep)
  - OCD62 overlap12 case 006 (sid=362) grok single_shot   (run5 = hard fail)
  - OCD62 overlap12 case 011 (sid=735) grok full           (range > 1 eV)
  - OCD62 overlap12 case 011 (sid=735) grok single_shot    (split runs)
  - OCD62 overlap12 case 005 (sid=201) grok single_shot    (range 2.03 eV)

Default seeds: 100, 200, 300, 400, 500.

Outputs:
  - CMU20: research/results/canonical_raw/cmu20_case20_grok4_oneshot_seed_sweep/
           seed_<N>/one_shot/20/
  - OCD62: research/results/canonical_raw/ocd62_overlap12_grok_outlier_seed_sweep_20260509/
           seed_<N>/<variant_dir>/<case>/
  - Summary CSV: research/results/canonical_raw/grok_outlier_seed_sweep_20260509_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from research.agent_eval.common import (  # noqa: E402
    ABLATED_VARIANTS,
    load_frozen_config,
    load_manifest_map,
)
from research.agent_eval.run_case import execute_case  # noqa: E402

CMU_MANIFEST = ROOT / "research/agent_eval/manifests/cmu_manifest.csv"
OCD62_MANIFEST = ROOT / "datasets/ocd62_overlap12/manifest.csv"
GROK_CONFIG = (
    ROOT
    / "research/results/run_configs/ocd62_run45/frozen_config_ocd62_run5_grok4_recovery_max2000.json"
)

CMU_SWEEP_ROOT = ROOT / "research/results/canonical_raw/cmu20_case20_grok4_oneshot_seed_sweep"
OCD62_SWEEP_ROOT = (
    ROOT / "research/results/canonical_raw/ocd62_overlap12_grok_outlier_seed_sweep_20260509"
)
SUMMARY_CSV = (
    ROOT / "research/results/canonical_raw/grok_outlier_seed_sweep_20260509_summary.csv"
)

VARIANT_FLAG_KEY: Dict[str, str] = {
    "full": "full",
    "no_slip": "no_slip",
    "no_forbid": "no_forbid",
    "no_termination": "no_termination",
    "one_shot": "single_shot",
    "single_shot": "single_shot",
}

DEFAULT_SEEDS: List[int] = [100, 200, 300, 400, 500]

TARGETS: List[Dict[str, Any]] = [
    {"set": "cmu20", "variant": "one_shot", "case_id": "20", "rationale": "grok one_shot=-6.04 vs -11.65 consensus"},
    {"set": "ocd62", "variant": "single_shot", "case_id": "006", "rationale": "sid=362 run5 hard failure"},
    {"set": "ocd62", "variant": "single_shot", "case_id": "005", "rationale": "sid=201 range 2.03 eV"},
    {"set": "ocd62", "variant": "full", "case_id": "011", "rationale": "sid=735 run5 -10.63 vs -11.66 consensus"},
    {"set": "ocd62", "variant": "single_shot", "case_id": "011", "rationale": "sid=735 split runs 1-3 vs 4-5"},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def out_root_for(target: Dict[str, Any], seed: int) -> Path:
    if target["set"] == "cmu20":
        return CMU_SWEEP_ROOT / f"seed_{seed}" / target["variant"]
    return OCD62_SWEEP_ROOT / f"seed_{seed}" / target["variant"]


def case_complete(case_dir: Path) -> bool:
    rp = case_dir / "result.json"
    if not rp.exists():
        return False
    try:
        d = json.loads(rp.read_text(encoding="utf-8"))
    except Exception:
        return False
    return d.get("status") == "success" and d.get("best_energy_eV") is not None


def run_one(
    target: Dict[str, Any],
    seed: int,
    manifest: Dict[str, Dict[str, str]],
    base_config: Dict[str, Any],
    api_key: Optional[str],
    dry_run: bool,
    force: bool,
) -> Dict[str, Any]:
    out_root = out_root_for(target, seed)
    out_root.mkdir(parents=True, exist_ok=True)
    case_dir = out_root / target["case_id"]

    if case_dir.exists() and case_complete(case_dir) and not force:
        rj = json.loads((case_dir / "result.json").read_text(encoding="utf-8"))
        return {
            "set": target["set"],
            "variant": target["variant"],
            "case_id": target["case_id"],
            "seed": seed,
            "status": "skipped_complete",
            "best_energy_eV": rj.get("best_energy_eV"),
            "iteration_count": rj.get("iteration_count"),
            "error": "",
        }

    if case_dir.exists():
        shutil.rmtree(case_dir)

    cfg = dict(base_config)
    cfg["random_seed"] = seed
    cfg["transport_variant"] = f"grok_outlier_sweep_seed{seed}_{target['set']}"
    cfg["notes"] = [
        "Grok-4 outlier seed sweep dated 2026-05-09 (advisor audit follow-up).",
        f"Reseeded for: {target['rationale']}",
        "Physics protocol stays MACE-MP-0 small / float32 / CPU / no dispersion / fmax=0.1.",
    ]

    runtime_key = VARIANT_FLAG_KEY[target["variant"]]
    runtime_overrides = ABLATED_VARIANTS[runtime_key]

    backoff_seconds = [60, 180, 300]
    last_payload: Dict[str, Any] = {}
    for attempt_idx in range(len(backoff_seconds) + 1):
        if attempt_idx > 0:
            wait = backoff_seconds[attempt_idx - 1]
            print(
                f"[{utc_now()}] RETRY set={target['set']} variant={target['variant']} "
                f"case={target['case_id']} seed={seed} attempt={attempt_idx + 1} "
                f"after_5xx_wait={wait}s",
                flush=True,
            )
            time.sleep(wait)
            if case_dir.exists():
                shutil.rmtree(case_dir)
        else:
            print(
                f"[{utc_now()}] RUN set={target['set']} variant={target['variant']} "
                f"case={target['case_id']} seed={seed}",
                flush=True,
            )

        res = execute_case(
            case_row=manifest[target["case_id"]],
            frozen_config=cfg,
            output_root=out_root,
            runtime_overrides=runtime_overrides,
            explicit_api_key=api_key if not dry_run else None,
            dry_run=dry_run,
            repo_root=str(ROOT),
        )
        last_payload = res.result
        err = (last_payload.get("error") or "").lower()
        is_5xx = any(token in err for token in ("'code': 50", "code\":50", "internal server error", "service temporarily unavailable", "bad gateway", "service unavailable", "gateway timeout"))
        if not is_5xx:
            break

    return {
        "set": target["set"],
        "variant": target["variant"],
        "case_id": target["case_id"],
        "seed": seed,
        "status": last_payload.get("status"),
        "best_energy_eV": last_payload.get("best_energy_eV"),
        "iteration_count": last_payload.get("iteration_count"),
        "error": last_payload.get("error") or "",
    }


def write_summary(rows: List[Dict[str, Any]]) -> None:
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    keys = [
        "set",
        "variant",
        "case_id",
        "seed",
        "status",
        "best_energy_eV",
        "iteration_count",
        "error",
    ]
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in keys})


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS))
    p.add_argument("--filter-set", choices=["all", "cmu20", "ocd62"], default="all")
    p.add_argument(
        "--targets",
        default="",
        help="Comma list of target indices (0-based) into TARGETS to run; default all",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="Re-run even if seed/case already complete")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not args.dry_run and not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required for non-dry runs.")

    cmu_manifest = load_manifest_map(CMU_MANIFEST)
    ocd62_manifest = load_manifest_map(OCD62_MANIFEST)
    base_config = load_frozen_config(GROK_CONFIG)

    indices = (
        [int(x) for x in args.targets.split(",") if x.strip()]
        if args.targets
        else list(range(len(TARGETS)))
    )
    selected = [TARGETS[i] for i in indices]
    if args.filter_set != "all":
        selected = [t for t in selected if t["set"] == args.filter_set]

    print(f"[{utc_now()}] selected_targets={[t for t in selected]} seeds={seeds}", flush=True)

    rows: List[Dict[str, Any]] = []
    for target in selected:
        manifest = cmu_manifest if target["set"] == "cmu20" else ocd62_manifest
        for seed in seeds:
            t0 = time.perf_counter()
            try:
                row = run_one(
                    target=target,
                    seed=seed,
                    manifest=manifest,
                    base_config=base_config,
                    api_key=api_key,
                    dry_run=args.dry_run,
                    force=args.force,
                )
            except Exception as exc:
                row = {
                    "set": target["set"],
                    "variant": target["variant"],
                    "case_id": target["case_id"],
                    "seed": seed,
                    "status": "exception",
                    "best_energy_eV": None,
                    "iteration_count": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(f"[{utc_now()}] EXC {row}", flush=True)
            dt = time.perf_counter() - t0
            print(
                f"[{utc_now()}] DONE set={row['set']} variant={row['variant']} "
                f"case={row['case_id']} seed={row['seed']} status={row['status']} "
                f"E={row['best_energy_eV']} dt={dt:.1f}s",
                flush=True,
            )
            rows.append(row)
            write_summary(rows)

    print(f"[{utc_now()}] SUMMARY {SUMMARY_CSV}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
