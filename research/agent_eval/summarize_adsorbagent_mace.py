"""Summarize Adsorb-Agent MACE runs and compare against AdsMind full runs."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import yaml
from ase import Atoms
from ase.constraints import FixAtoms
from ase.io import read
from ase.optimize import BFGS

try:
    import torch

    if not hasattr(torch.compiler, "is_compiling"):
        torch.compiler.is_compiling = lambda: False  # type: ignore[attr-defined]
except Exception:
    pass

from mace.calculators import mace_mp
from scipy.stats import wilcoxon

from research.agent_eval.common import (
    benjamini_hochberg,
    compute_bootstrap_ci,
    exact_mcnemar,
    rank_biserial_from_differences,
)
from research.agent_eval.experiment_identity import backend_identity, summary_metadata


SUMMARY_FIELDS = [
    "baseline",
    "backend_key",
    "backend",
    "llm_model",
    "force_field",
    "calculator_backend",
    "force_field_model",
    "force_field_size",
    "max_config_budget",
    "random_ratio",
    "case_id",
    "config_name",
    "ads_smiles",
    "bulk_symbol",
    "bulk_id",
    "miller",
    "shift",
    "top",
    "status",
    "skip_reason",
    "traj_count",
    "valid_traj_count",
    "best_total_energy",
    "best_adsorption_energy_eV",
    "best_config",
    "adsorbagent_configs_tested",
    "critic_loop_count",
    "llm_token_count",
    "llm_prompt_tokens",
    "llm_completion_tokens",
    "llm_successful_requests",
    "llm_total_cost_usd",
    "site_type",
    "site_atoms",
    "ads_bind_atoms",
    "orient",
    "cutoff_multiplier",
]

ADSORBAGENT_METADATA = {
    "baseline": "adsorbagent",
    **summary_metadata(backend_identity("gpt")),
}


COMPARISON_FIELDS = [
    "case_id",
    "surface",
    "adsorbate",
    "adsmind_best_energy",
    "adsmind_iterations",
    "adsmind_success",
    "adsmind_slip_count",
    "adsmind_dissociation",
    "adsorbagent_best_energy",
    "adsorbagent_success",
    "adsorbagent_configs_tested",
    "adsorbagent_valid_configs",
    "adsorbagent_llm_tokens",
    "energy_diff",
    "winner",
    "notes",
]


def parse_optional_float(value: Any) -> Optional[float]:
    """Parse a float-like value, returning None for blanks."""
    if value is None or value == "":
        return None
    return float(value)


def parse_bool(value: Any) -> bool:
    """Parse a common boolean-like value."""
    return str(value).strip().lower() in {"1", "true", "yes", "y", "success"}


def normalize_case_id(value: Any) -> str:
    """Normalize numeric-looking case IDs without truncating existing padding."""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    width = max(2, len(text))
    return text.zfill(width)


def load_csv(path: Path) -> List[Dict[str, str]]:
    """Load a CSV file as dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    """Write rows as CSV with stable field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_case_config(config_dir: Path, config_name: str) -> Dict[str, Any]:
    """Load one Adsorb-Agent per-system YAML config."""
    path = config_dir / f"{config_name}.yaml"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle).get("system_info", {})


def load_result_payload(result_dir: Path) -> Dict[str, Any]:
    """Load result.pkl if present."""
    result_path = result_dir / "result.pkl"
    if not result_path.exists():
        return {}
    with result_path.open("rb") as handle:
        return pickle.load(handle)


def get_mace_calc():
    """Return the MACE-MP small CPU float32 calculator used by the experiment."""
    return mace_mp(model="small", device="cpu", default_dtype="float32")


def split_initial_adslab(initial: Atoms) -> Tuple[Atoms, Atoms]:
    """Split an initial adslab into bare surface and adsorbate atoms by tags."""
    tags = np.asarray(initial.get_tags())
    if not np.any(tags == 2):
        raise ValueError("initial structure has no adsorbate atoms tagged as 2")
    surface = initial[tags != 2]
    adsorbate = initial[tags == 2]
    surface.set_cell(initial.cell)
    surface.set_pbc(initial.pbc)
    adsorbate.set_cell([20.0, 20.0, 20.0])
    adsorbate.set_pbc([False, False, False])
    adsorbate.center()
    return surface, adsorbate


def reference_energies(initial: Atoms, calc, fmax: float, steps: int) -> Tuple[float, float]:
    """Compute bare-surface and isolated-adsorbate reference energies."""
    surface, adsorbate = split_initial_adslab(initial)
    surface.calc = calc
    surface.set_constraint(FixAtoms(indices=list(range(len(surface)))))
    e_surface = float(surface.get_potential_energy())

    adsorbate.calc = calc
    adsorbate.set_constraint()
    if len(adsorbate) > 1:
        BFGS(adsorbate, trajectory=None, logfile=None).run(fmax=fmax, steps=steps)
    e_adsorbate = float(adsorbate.get_potential_energy())
    return e_surface, e_adsorbate


def format_list(value: Any) -> str:
    """Stable string for list-like result fields."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ";".join(str(item) for item in value)
    return str(value)


def summarize_case(
    result_dir: Path,
    config_dir: Path,
    calc,
    detect_anomaly_cls,
    fmax: float,
    steps: int,
) -> Dict[str, Any]:
    """Summarize one Adsorb-Agent result directory."""
    config_name = result_dir.name
    case_id = normalize_case_id(config_name.split("_", 1)[0])
    cfg = load_case_config(config_dir, config_name)
    payload = load_result_payload(result_dir)
    solution = payload.get("initial_solution", {}) if payload else {}

    row: Dict[str, Any] = {
        **ADSORBAGENT_METADATA,
        "max_config_budget": payload.get("max_config_budget", ""),
        "random_ratio": payload.get("random_ratio", ""),
        "case_id": case_id,
        "config_name": config_name,
        "ads_smiles": cfg.get("ads_smiles", ""),
        "bulk_symbol": cfg.get("bulk_symbol", ""),
        "bulk_id": cfg.get("bulk_id", ""),
        "miller": cfg.get("miller", ""),
        "shift": cfg.get("shift", ""),
        "top": cfg.get("top", ""),
        "status": "skipped",
        "skip_reason": "",
        "traj_count": 0,
        "valid_traj_count": 0,
        "best_total_energy": "",
        "best_adsorption_energy_eV": "",
        "best_config": "",
        "adsorbagent_configs_tested": payload.get("config_no_count", ""),
        "critic_loop_count": payload.get("critic_loop_count", ""),
        "llm_token_count": payload.get("llm_token_count", ""),
        "llm_prompt_tokens": payload.get("llm_prompt_tokens", ""),
        "llm_completion_tokens": payload.get("llm_completion_tokens", ""),
        "llm_successful_requests": payload.get("llm_successful_requests", ""),
        "llm_total_cost_usd": payload.get("llm_total_cost_usd", ""),
        "site_type": solution.get("site_type", ""),
        "site_atoms": format_list(solution.get("site_atoms")),
        "ads_bind_atoms": format_list(solution.get("ads_bind_atoms")),
        "orient": solution.get("orient", ""),
        "cutoff_multiplier": payload.get("cutoff_multiplier", ""),
    }

    traj_dir = result_dir / "traj"
    traj_files = sorted(traj_dir.glob("*.traj")) if traj_dir.exists() else []
    row["traj_count"] = len(traj_files)
    if not traj_files:
        row["skip_reason"] = "no_traj_files"
        return row

    try:
        first_traj = read(traj_files[0], index=":")
        e_surface, e_adsorbate = reference_energies(first_traj[0], calc, fmax, steps)
    except Exception as exc:
        row["status"] = "error"
        row["skip_reason"] = f"reference_energy_error: {exc}"
        return row

    valid: List[Tuple[str, float, float]] = []
    anomalies = {"dissociated": 0, "desorbed": 0, "surface_changed": 0, "read_error": 0}
    for traj_file in traj_files:
        try:
            traj = read(traj_file, index=":")
            initial = traj[0]
            final = traj[-1]
            detector = detect_anomaly_cls(initial, final, initial.get_tags())
            dissociated = detector.is_adsorbate_dissociated()
            desorbed = detector.is_adsorbate_desorbed()
            surface_changed = detector.has_surface_changed()
            if dissociated:
                anomalies["dissociated"] += 1
            if desorbed:
                anomalies["desorbed"] += 1
            if surface_changed:
                anomalies["surface_changed"] += 1
            if not (dissociated or desorbed or surface_changed):
                total_energy = float(final.get_potential_energy())
                adsorption_energy = total_energy - e_surface - e_adsorbate
                valid.append((traj_file.stem, total_energy, adsorption_energy))
        except Exception:
            anomalies["read_error"] += 1

    row["valid_traj_count"] = len(valid)
    if not valid:
        row["status"] = "failed"
        row["skip_reason"] = json.dumps(anomalies, sort_keys=True)
        return row

    best_config, best_total, best_ads = min(valid, key=lambda item: item[2])
    row["status"] = "success"
    row["best_config"] = best_config
    row["best_total_energy"] = best_total
    row["best_adsorption_energy_eV"] = best_ads
    row["skip_reason"] = json.dumps(anomalies, sort_keys=True)
    return row


def summarize_adsorbagent(
    results_dir: Path,
    config_dir: Path,
    catalyst_root: Path,
    fmax: float,
    steps: int,
) -> List[Dict[str, Any]]:
    """Summarize all Adsorb-Agent case result directories."""
    sys.path.insert(0, str(catalyst_root))
    from tools import DetectTrajAnomaly  # type: ignore

    calc = get_mace_calc()
    rows = []
    for result_dir in sorted(path for path in results_dir.iterdir() if path.is_dir()):
        rows.append(summarize_case(result_dir, config_dir, calc, DetectTrajAnomaly, fmax, steps))
    return rows


def compare_with_adsmind(
    adsorbagent_rows: Iterable[Dict[str, Any]],
    adsmind_summary: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Build comparison rows and statistical payload."""
    adsmind_rows = {
        normalize_case_id(row["case_id"]): row
        for row in load_csv(adsmind_summary)
        if row.get("variant") == "full"
    }
    competitor_rows = {normalize_case_id(row["case_id"]): row for row in adsorbagent_rows}

    comparison_rows: List[Dict[str, Any]] = []
    energy_differences: List[float] = []
    success_pairs = []

    for case_id in sorted(set(adsmind_rows) & set(competitor_rows)):
        ours = adsmind_rows[case_id]
        theirs = competitor_rows[case_id]
        ours_energy = parse_optional_float(ours.get("best_energy", ""))
        theirs_energy = parse_optional_float(theirs.get("best_adsorption_energy_eV", ""))
        ours_success = parse_bool(ours.get("success", ""))
        theirs_success = theirs.get("status") == "success"
        success_pairs.append((ours_success, theirs_success))

        energy_diff = None
        winner = "tie"
        if ours_energy is not None and theirs_energy is not None:
            energy_diff = ours_energy - theirs_energy
            energy_differences.append(energy_diff)
            if energy_diff < 0:
                winner = "adsmind"
            elif energy_diff > 0:
                winner = "adsorbagent"

        comparison_rows.append(
            {
                "case_id": case_id,
                "surface": theirs.get("bulk_symbol", ""),
                "adsorbate": theirs.get("ads_smiles", ""),
                "adsmind_best_energy": ours_energy,
                "adsmind_iterations": int(ours.get("iterations") or 0),
                "adsmind_success": ours_success,
                "adsmind_slip_count": int(ours.get("slip_count") or 0),
                "adsmind_dissociation": int(ours.get("dissociation_count") or 0),
                "adsorbagent_best_energy": theirs_energy,
                "adsorbagent_success": theirs_success,
                "adsorbagent_configs_tested": int(theirs.get("traj_count") or 0),
                "adsorbagent_valid_configs": int(theirs.get("valid_traj_count") or 0),
                "adsorbagent_llm_tokens": int(theirs.get("llm_token_count") or 0),
                "energy_diff": energy_diff,
                "winner": winner,
                "notes": theirs.get("skip_reason", ""),
            }
        )

    stats_payload: Dict[str, Any] = {
        "num_cases": len(comparison_rows),
        "num_energy_pairs": len(energy_differences),
        "energy_diff_definition": "adsmind_best_energy - adsorbagent_best_energy",
        "wilcoxon": None,
        "mcnemar": exact_mcnemar(success_pairs),
        "rank_biserial": rank_biserial_from_differences(energy_differences),
        "bootstrap_ci": compute_bootstrap_ci(energy_differences),
    }
    if len(energy_differences) >= 2:
        result = wilcoxon(energy_differences, alternative="two-sided", zero_method="wilcox")
        stats_payload["wilcoxon"] = {
            "statistic": float(result.statistic),
            "p_value": float(result.pvalue),
        }

    raw_p_values = {
        "wilcoxon": stats_payload["wilcoxon"]["p_value"] if stats_payload["wilcoxon"] else None,
        "mcnemar": stats_payload["mcnemar"]["p_value"] if stats_payload["mcnemar"] else None,
    }
    stats_payload["benjamini_hochberg"] = benjamini_hochberg(raw_p_values)
    return comparison_rows, stats_payload


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adsorbagent-results", required=True, type=Path)
    parser.add_argument("--adsorbagent-config-dir", required=True, type=Path)
    parser.add_argument("--catalyst-root", required=True, type=Path)
    parser.add_argument("--adsmind-summary", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--stats-output", type=Path)
    parser.add_argument("--fmax", type=float, default=0.10)
    parser.add_argument("--steps", type=int, default=200)
    args = parser.parse_args(argv)

    adsorbagent_rows = summarize_adsorbagent(
        args.adsorbagent_results,
        args.adsorbagent_config_dir,
        args.catalyst_root,
        args.fmax,
        args.steps,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.csv"
    write_csv(summary_path, adsorbagent_rows, SUMMARY_FIELDS)

    comparison_rows, stats_payload = compare_with_adsmind(adsorbagent_rows, args.adsmind_summary)
    comparison_path = args.output_dir / "comparison.csv"
    stats_path = args.output_dir / "comparison_stats.json"
    write_csv(comparison_path, comparison_rows, COMPARISON_FIELDS)
    with stats_path.open("w", encoding="utf-8") as handle:
        json.dump(stats_payload, handle, indent=2, ensure_ascii=False)
    if args.stats_output is not None:
        args.stats_output.parent.mkdir(parents=True, exist_ok=True)
        with args.stats_output.open("w", encoding="utf-8") as handle:
            json.dump(stats_payload, handle, indent=2, ensure_ascii=False)

    print(summary_path)
    print(comparison_path)
    print(stats_path)
    if args.stats_output is not None:
        print(args.stats_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
