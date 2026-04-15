"""Robust Gemini OCD-GMAE recovery with provider fallback and final rebuilds."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_ALL = ["003", "004", "023", "024", "005", "019", "015", "013", "012", "016"]
VARIANTS = ["full", "no_slip", "no_forbid", "no_termination"]
VARIANTS_WITH_ONE_SHOT = VARIANTS + ["single_shot"]
PRIMARY_SESSION = "ocd_gem_recover"
PRIMARY_LOG = Path("/tmp/ocd_gem_recover.log")
STALE_SECONDS = 20 * 60
POLL_SECONDS = 60

ABLATION_DIR = REPO_ROOT / "research/results/ocd_gmae_gemini_ablation_v1"
ONE_SHOT_DIR = REPO_ROOT / "research/results/ocd_gmae_v1_gemini_one_shot"
GLOBAL_SUMMARY_CSV = REPO_ROOT / "research/results/ocd_gmae_ablation_multi_backend_final.csv"
GLOBAL_SUMMARY_JSON = REPO_ROOT / "research/results/ocd_gmae_ablation_multi_backend_final.json"
GLOBAL_COMPARE_CSV = REPO_ROOT / "research/results/ocd_gmae_ablation_final_vs_one_shot_4backend.csv"
FAILED_CELLS_CSV = REPO_ROOT / "research/results/ocd_gmae_gemini_ablation_failed_cells.csv"

OPENROUTER_CONFIG = REPO_ROOT / "research/agent_eval/configs/frozen_config_gemini25pro_openrouter.json"
AIHUBMIX_CONFIG = REPO_ROOT / "research/agent_eval/configs/frozen_config_gemini25pro.json"
MANIFEST_PATH = REPO_ROOT / "research/agent_eval/manifests/ocd_gmae_manifest.csv"

BACKEND_SUMMARIES = {
    "gemini": ABLATION_DIR / "ablation_summary.csv",
    "grok": REPO_ROOT / "research/results/ocd_gmae_xai_grok4_ablation_v1/ablation_summary.csv",
    "gpt54": REPO_ROOT / "research/results/ocd_gmae_openai_gpt54_ablation_v1/ablation_summary.csv",
    "claude": REPO_ROOT / "research/results/ocd_gmae_anthropic_sonnet46_ablation_v1/ablation_summary.csv",
}
ONE_SHOT_SUMMARIES = {
    "gemini": REPO_ROOT / "research/results/ocd_gmae_v1_gemini_one_shot/summary.csv",
    "grok": REPO_ROOT / "research/results/ocd_gmae_v1_xai_grok4_one_shot/summary.csv",
    "gpt54": REPO_ROOT / "research/results/ocd_gmae_v1_openai_gpt54_one_shot/summary.csv",
    "claude": REPO_ROOT / "research/results/ocd_gmae_v1_anthropic_sonnet46_one_shot/summary.csv",
}


def log(message: str) -> None:
    print(f"[gemini-robust] {message}", flush=True)


def run_command(cmd: List[str]) -> None:
    log("RUN " + " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def load_env_from_shell_files() -> None:
    pattern = re.compile(r'^\s*export\s+(OPENROUTER_API_KEY|AIHUBMIX_API_KEY)=["\']?([^"\']+)')
    for path in (Path.home() / ".zshrc", Path.home() / ".zprofile", Path.home() / ".bashrc"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.lstrip().startswith("#"):
                continue
            match = pattern.match(line)
            if not match:
                continue
            key, value = match.groups()
            if value:
                os.environ[key] = value


def tmux_session_exists(name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def kill_tmux_session(name: str) -> None:
    subprocess.run(
        ["tmux", "kill-session", "-t", name],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def wait_for_primary_session() -> None:
    if not tmux_session_exists(PRIMARY_SESSION):
        return

    log(f"waiting for active tmux session {PRIMARY_SESSION}")
    while tmux_session_exists(PRIMARY_SESSION):
        if PRIMARY_LOG.exists():
            age = time.time() - PRIMARY_LOG.stat().st_mtime
            if age > STALE_SECONDS:
                log(
                    f"{PRIMARY_SESSION} appears stale "
                    f"({int(age)}s without log update); killing and taking over"
                )
                kill_tmux_session(PRIMARY_SESSION)
                break
        time.sleep(POLL_SECONDS)


def rebuild_gemini_summary() -> None:
    run_command(
        [
            sys.executable,
            "-m",
            "research.agent_eval.rebuild_ablation_summary",
            "--ablation-dir",
            str(ABLATION_DIR),
            "--one-shot-dir",
            str(ONE_SHOT_DIR),
            "--cases",
            ",".join(CASES_ALL),
            "--variants",
            ",".join(VARIANTS_WITH_ONE_SHOT),
        ]
    )


def summarize_global() -> None:
    cmd = [
        sys.executable,
        "-m",
        "research.agent_eval.summarize_multi_backend_ablation",
    ]
    for label, path in BACKEND_SUMMARIES.items():
        cmd.extend(["--summary", f"{label}={path}"])
    cmd.extend(["--output-csv", str(GLOBAL_SUMMARY_CSV), "--output-json", str(GLOBAL_SUMMARY_JSON)])
    run_command(cmd)


def write_one_shot_comparison() -> None:
    def parse_float(value: str | None) -> float | None:
        if value in (None, "", "None"):
            return None
        return float(value)

    one_shot: Dict[str, Dict[str, float | None]] = {}
    for label, path in ONE_SHOT_SUMMARIES.items():
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                energy = parse_float(row.get("best_energy_eV")) if row.get("status") == "success" else None
                one_shot.setdefault(row["case_id"], {})[label] = energy

    with GLOBAL_SUMMARY_CSV.open("r", encoding="utf-8", newline="") as handle:
        ablation_rows = {(row["case_id"], row["variant"]): row for row in csv.DictReader(handle)}

    rows = []
    for case_id in CASES_ALL:
        one_shot_values = [value for value in one_shot.get(case_id, {}).values() if value is not None]
        one_shot_range = max(one_shot_values) - min(one_shot_values) if len(one_shot_values) >= 2 else None
        best_variant = None
        best_range = None
        for variant in VARIANTS:
            row = ablation_rows[(case_id, variant)]
            range_best_energy = parse_float(row.get("range_best_energy"))
            if range_best_energy is None:
                continue
            if best_range is None or range_best_energy < best_range:
                best_variant = variant
                best_range = range_best_energy
        rows.append(
            {
                "case_id": case_id,
                "one_shot_range_4backend": one_shot_range,
                "best_closed_loop_variant_4backend": best_variant,
                "best_closed_loop_range_4backend": best_range,
                "range_delta_vs_one_shot_4backend": (
                    None if one_shot_range is None or best_range is None else best_range - one_shot_range
                ),
            }
        )

    with GLOBAL_COMPARE_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    log(f"wrote {GLOBAL_COMPARE_CSV}")


def refresh_all_outputs() -> None:
    rebuild_gemini_summary()
    summarize_global()
    write_one_shot_comparison()


def load_pending_failures() -> Dict[str, List[str]]:
    summary_path = ABLATION_DIR / "ablation_summary.csv"
    pending: Dict[str, List[str]] = {variant: [] for variant in VARIANTS}

    if not summary_path.exists():
        pending["full"] = ["012", "016"]
        for variant in ("no_slip", "no_forbid", "no_termination"):
            pending[variant] = list(CASES_ALL)
        return pending

    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        variant = row["variant"]
        if variant not in pending:
            continue
        if row["case_id"] not in CASES_ALL:
            continue
        if row.get("success") != "True":
            pending[variant].append(row["case_id"])
    return pending


def write_failed_cells_csv(pending: Dict[str, Iterable[str]]) -> None:
    rows = [
        {"case_id": case_id, "variant": variant}
        for variant, case_ids in pending.items()
        for case_id in case_ids
    ]
    with FAILED_CELLS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "variant"])
        writer.writeheader()
        writer.writerows(rows)
    log(f"wrote {FAILED_CELLS_CSV} with {len(rows)} rows")


def run_pending_for_config(config_path: Path, pending: Dict[str, List[str]]) -> None:
    for variant in VARIANTS:
        case_ids = pending.get(variant, [])
        if not case_ids:
            continue
        run_command(
            [
                sys.executable,
                "-m",
                "research.agent_eval.run_ablation",
                "--manifest",
                str(MANIFEST_PATH),
                "--config",
                str(config_path),
                "--output",
                str(ABLATION_DIR),
                "--cases",
                ",".join(case_ids),
                "--variants",
                variant,
            ]
        )
        rebuild_gemini_summary()


def available_provider_configs() -> List[Path]:
    load_env_from_shell_files()
    providers: List[Path] = []
    if os.environ.get("OPENROUTER_API_KEY"):
        providers.append(OPENROUTER_CONFIG)
    if os.environ.get("AIHUBMIX_API_KEY"):
        providers.append(AIHUBMIX_CONFIG)
    return providers


def main() -> int:
    wait_for_primary_session()
    refresh_all_outputs()

    pending = load_pending_failures()
    write_failed_cells_csv(pending)
    remaining = sum(len(case_ids) for case_ids in pending.values())
    if remaining == 0:
        log("nothing left to recover")
        return 0

    provider_configs = available_provider_configs()
    if not provider_configs:
        log("no recovery provider is configured; leaving failed cells for manual rerun")
        return 1

    for config_path in provider_configs:
        pending = load_pending_failures()
        remaining = sum(len(case_ids) for case_ids in pending.values())
        if remaining == 0:
            break
        log(f"attempting {remaining} failed cells with {config_path.name}")
        run_pending_for_config(config_path, pending)
        refresh_all_outputs()
        write_failed_cells_csv(load_pending_failures())

    pending = load_pending_failures()
    remaining = sum(len(case_ids) for case_ids in pending.values())
    if remaining == 0:
        log("recovery finished successfully")
        return 0

    log(f"recovery finished with {remaining} failed cells remaining")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
