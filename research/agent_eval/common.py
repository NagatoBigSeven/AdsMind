"""Shared helpers for AdsMind agent-side experiments."""

from __future__ import annotations

import csv
import io
import json
import logging
import shutil
import subprocess
import traceback
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

from langchain_core.messages import AIMessage
from scipy.stats import binomtest, bootstrap, rankdata

from adsmind.agent.agent import _prepare_initial_state
from adsmind.tools.common import ensure_output_dir
from adsmind.utils.config import get_api_key_for_backend
from research.agent_eval.experiment_identity import identity_from_path, summary_metadata

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_RECURSION_LIMIT = 50
DEFAULT_RESULT_NAME = "result.json"
SUMMARY_COLUMNS = [
    "backend_key",
    "backend",
    "llm_model",
    "force_field",
    "calculator_backend",
    "force_field_model",
    "force_field_size",
    "case_id",
    "slab_file",
    "smiles",
    "user_request",
    "surface_family",
    "adsorbate_name",
    "miller_index",
    "reaction_class",
    "status",
    "best_energy_eV",
    "iteration_count",
    "max_attempts",
    "perfect_count",
    "dissociation_count",
    "rearrangement_count",
    "calc_failure_count",
    "chemical_slip_count",
    "final_site_type",
    "converged_tag",
    "wall_clock_sec",
    "total_input_tokens",
    "total_output_tokens",
    "best_structure_file",
    "generated_conformers_file",
    "relaxation_trajectory_file",
]
ABLATED_VARIANTS = {
    "full": {
        "enable_slip_feedback": True,
        "enable_forbid": True,
        "enable_termination": True,
        "max_attempts": 5,
    },
    "no_slip": {
        "enable_slip_feedback": False,
        "enable_forbid": False,
        "enable_termination": True,
        "max_attempts": 5,
    },
    "no_forbid": {
        "enable_slip_feedback": True,
        "enable_forbid": False,
        "enable_termination": True,
        "max_attempts": 5,
    },
    "no_termination": {
        "enable_slip_feedback": True,
        "enable_forbid": True,
        "enable_termination": False,
        "max_attempts": 5,
    },
    "single_shot": {
        "enable_slip_feedback": False,
        "enable_forbid": False,
        "enable_termination": False,
        "max_attempts": 1,
    },
    "one_shot": {
        "enable_slip_feedback": False,
        "enable_forbid": False,
        "enable_termination": False,
        "max_attempts": 1,
    },
    "no_executor": {
        "enable_slip_feedback": True,
        "enable_forbid": True,
        "enable_termination": True,
        "enable_executor": False,
        "enable_validator": True,
        "max_attempts": 5,
    },
    "no_validator": {
        "enable_slip_feedback": True,
        "enable_forbid": True,
        "enable_termination": True,
        "enable_executor": True,
        "enable_validator": False,
        "max_attempts": 5,
    },
}


@dataclass
class CaseRunResult:
    """Structured handle for a case execution."""

    case_dir: Path
    config_path: Path
    result_path: Path
    log_path: Path
    result: Dict[str, Any]


def get_repo_root() -> Path:
    """Return the AdsMind repository root for research-side tools."""
    return REPO_ROOT


def resolve_repo_path(path: Path | str, repo_root: Path | str | None = None) -> Path:
    """Resolve a path from cwd first, then fall back to the repo root.

    The research scripts are often launched from nested directories on remote
    machines while their CLI examples use repo-root-relative paths.
    """
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    root = Path(repo_root).resolve() if repo_root is not None else get_repo_root()
    return (root / candidate).resolve()


def load_manifest(path: Path | str) -> List[Dict[str, str]]:
    """Load the CMU manifest while preserving string case IDs."""
    manifest_path = resolve_repo_path(path)
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            row = {key: (value or "") for key, value in row.items()}
            row["case_id"] = row["case_id"].zfill(2)
            rows.append(row)
    return rows


def load_manifest_map(path: Path | str) -> Dict[str, Dict[str, str]]:
    """Load the manifest and index it by case id."""
    return {row["case_id"]: row for row in load_manifest(path)}


def load_frozen_config(path: Path | str) -> Dict[str, Any]:
    """Load the experiment config."""
    config_path = resolve_repo_path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def current_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_git_sha(repo_root: Path | str) -> str:
    """Return the current git SHA, or 'unknown' if unavailable."""
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            text=True,
        )
        return output.strip()
    except Exception:
        return "unknown"


def resolve_runtime_flags(
    frozen_config: Dict[str, Any],
    runtime_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Resolve runtime state overrides from the frozen config plus local overrides."""
    overrides = dict(runtime_overrides or {})
    llm_extra_options = dict(frozen_config.get("llm_extra_options", {}))
    if frozen_config.get("llm_base_url"):
        llm_extra_options["base_url"] = frozen_config["llm_base_url"]
    if frozen_config.get("llm_default_headers"):
        llm_extra_options["default_headers"] = frozen_config["llm_default_headers"]
    if frozen_config.get("llm_seed") is not None:
        llm_extra_options["seed"] = frozen_config["llm_seed"]

    relaxation_config = {
        "fmax": frozen_config.get("fmax"),
        "steps": frozen_config.get("steps"),
        "md_steps": frozen_config.get("md_steps"),
        "md_temp": frozen_config.get("md_temp"),
    }
    relaxation_config = {
        key: value for key, value in relaxation_config.items() if value is not None
    }

    return {
        "llm_backend": frozen_config["llm_backend"],
        "llm_config": {
            "model": frozen_config["llm_model"],
            "temperature": frozen_config.get("temperature", 0.0),
            "max_tokens": frozen_config.get("max_tokens", 4096),
            "timeout": frozen_config.get("timeout_sec", 120),
            "extra_options": llm_extra_options,
        },
        "calculator_backend": frozen_config.get("calculator_backend", "mace"),
        "calculator_config": {
            "device": frozen_config.get("mace_device", "cpu"),
            "model": frozen_config.get("mace_model", "small"),
            "precision": frozen_config.get("mace_precision", "float32"),
            "use_dispersion": frozen_config.get("mace_use_dispersion", False),
        },
        "relaxation_config": relaxation_config,
        "random_seed": frozen_config.get("random_seed", 42),
        "relaxation_mode": frozen_config.get("relaxation_mode", "standard"),
        "enable_slip_feedback": overrides.get("enable_slip_feedback", True),
        "enable_forbid": overrides.get("enable_forbid", True),
        "enable_termination": overrides.get("enable_termination", True),
        "enable_executor": overrides.get("enable_executor", True),
        "enable_validator": overrides.get("enable_validator", True),
        "max_attempts": overrides.get(
            "max_attempts",
            frozen_config.get("max_retries", 5),
        ),
    }


def resolve_api_key(
    frozen_config: Dict[str, Any],
    explicit_api_key: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve the API key for the configured backend.

    Resolution order:
    1. ``explicit_api_key`` argument (e.g. from ``--api-key`` CLI flag)
    2. Environment variable named in ``frozen_config["llm_api_key_env_var"]``
    3. Default backend-specific lookup via :func:`get_api_key_for_backend`
    """
    if explicit_api_key:
        return explicit_api_key, "explicit"
    custom_env_var = frozen_config.get("llm_api_key_env_var")
    if custom_env_var:
        import os
        value = os.environ.get(custom_env_var)
        if value:
            return value, f"env:{custom_env_var}"
    return get_api_key_for_backend(frozen_config["llm_backend"])


def build_initial_state_for_case(
    case_row: Dict[str, str],
    frozen_config: Dict[str, Any],
    session_id: str,
    api_key: str,
    runtime_overrides: Optional[Dict[str, Any]] = None,
    repo_root: Path | str | None = None,
) -> Dict[str, Any]:
    """Construct the runtime initial state for a benchmark case."""
    runtime_flags = resolve_runtime_flags(frozen_config, runtime_overrides)
    return _prepare_initial_state(
        smiles=case_row["smiles"],
        slab_path=str(resolve_repo_path(case_row["slab_file"], repo_root=repo_root)),
        user_request=case_row["user_request"],
        api_key=api_key,
        session_id=session_id,
        **runtime_flags,
    )


def summarize_attempt_records(attempt_records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """Aggregate attempt-level counters used by summaries and stats."""
    perfect_count = 0
    dissociation_count = 0
    rearrangement_count = 0
    calc_failure_count = 0
    chemical_slip_count = 0

    for record in attempt_records:
        if record.get("status") != "success":
            calc_failure_count += 1
            continue
        if record.get("is_chemical_slip"):
            chemical_slip_count += 1
        if record.get("is_dissociated"):
            dissociation_count += 1
        elif (record.get("bond_change_count") or 0) > 0:
            rearrangement_count += 1
        else:
            perfect_count += 1

    return {
        "perfect_count": perfect_count,
        "dissociation_count": dissociation_count,
        "rearrangement_count": rearrangement_count,
        "calc_failure_count": calc_failure_count,
        "chemical_slip_count": chemical_slip_count,
    }


def build_result_payload(
    *,
    case_row: Dict[str, str],
    final_state: Optional[Dict[str, Any]],
    wall_clock_sec: float,
    artifact_paths: Dict[str, str],
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert the graph final state into a stable on-disk result schema."""
    final_state = final_state or {}
    attempt_records = list(final_state.get("attempt_records", []))
    last_analysis = {}
    raw_analysis = final_state.get("analysis_json")
    if isinstance(raw_analysis, str):
        try:
            last_analysis = json.loads(raw_analysis)
        except json.JSONDecodeError:
            last_analysis = {"status": "error", "message": raw_analysis}
    elif isinstance(raw_analysis, dict):
        last_analysis = raw_analysis

    best_result = final_state.get("best_result") or {}
    best_analysis = best_result.get("analysis_json", {}) if isinstance(best_result, dict) else {}
    counts = summarize_attempt_records(attempt_records)
    history = list(final_state.get("history", []))

    status = "error" if error else "failed"
    if best_result:
        status = "success"
    elif last_analysis.get("status") == "success":
        status = "failed"

    cleaned_error = None if status == "success" else error

    return {
        "case_id": case_row["case_id"],
        "case_metadata": case_row,
        "status": status,
        "best_energy_eV": best_result.get("most_stable_energy_eV"),
        "iteration_count": len(attempt_records),
        "max_attempts": final_state.get("max_attempts"),
        "final_site_type": best_analysis.get("site_analysis", {}).get("actual_site_type"),
        "converged_tag": any("Converged to known best" in entry for entry in history),
        "wall_clock_sec": wall_clock_sec,
        "total_input_tokens": final_state.get("total_input_tokens", 0),
        "total_output_tokens": final_state.get("total_output_tokens", 0),
        "artifact_paths": artifact_paths,
        "best_result": best_result,
        "last_analysis": last_analysis,
        "attempt_records": attempt_records,
        "history": history,
        "error": cleaned_error,
        **counts,
    }


def summary_row_from_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a case result into one summary row."""
    metadata = result.get("case_metadata", {})
    artifacts = result.get("artifact_paths", {})
    return {
        "case_id": metadata.get("case_id", result.get("case_id")),
        "slab_file": metadata.get("slab_file", ""),
        "smiles": metadata.get("smiles", ""),
        "user_request": metadata.get("user_request", ""),
        "surface_family": metadata.get("surface_family", ""),
        "adsorbate_name": metadata.get("adsorbate_name", ""),
        "miller_index": metadata.get("miller_index", ""),
        "reaction_class": metadata.get("reaction_class", ""),
        "status": result.get("status", "error"),
        "best_energy_eV": result.get("best_energy_eV"),
        "iteration_count": result.get("iteration_count", 0),
        "max_attempts": result.get("max_attempts"),
        "perfect_count": result.get("perfect_count", 0),
        "dissociation_count": result.get("dissociation_count", 0),
        "rearrangement_count": result.get("rearrangement_count", 0),
        "calc_failure_count": result.get("calc_failure_count", 0),
        "chemical_slip_count": result.get("chemical_slip_count", 0),
        "final_site_type": result.get("final_site_type"),
        "converged_tag": result.get("converged_tag", False),
        "wall_clock_sec": result.get("wall_clock_sec"),
        "total_input_tokens": result.get("total_input_tokens", 0),
        "total_output_tokens": result.get("total_output_tokens", 0),
        "best_structure_file": artifacts.get("best_structure_file", ""),
        "generated_conformers_file": artifacts.get("generated_conformers_file", ""),
        "relaxation_trajectory_file": artifacts.get("relaxation_trajectory_file", ""),
    }


def write_json(path: Path | str, payload: Dict[str, Any]) -> None:
    """Write UTF-8 JSON with stable formatting."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def copy_session_artifacts(session_id: str, case_dir: Path) -> Dict[str, str]:
    """Copy the generated session outputs into the case directory."""
    session_dir = ensure_output_dir(session_id)
    artifacts_dir = case_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    copied: Dict[str, str] = {}
    if not session_dir.exists():
        return copied

    for source in sorted(session_dir.iterdir()):
        if not source.is_file():
            continue
        target = artifacts_dir / source.name
        shutil.copy2(source, target)
        copied[source.stem] = str(target)
        copied[source.name] = str(target)
        if source.name.startswith("BEST_"):
            copied["best_structure_file"] = str(target)
        elif source.name == "summary_report.md":
            copied["summary_report_file"] = str(target)
        elif source.name == "best_configuration.png":
            copied["best_configuration_png"] = str(target)
        elif source.name == "iteration_energy_curve.png":
            copied["iteration_energy_curve_png"] = str(target)
        elif source.suffix == ".traj" and "generated_conformers" in source.name:
            copied["generated_conformers_file"] = str(target)
        elif source.suffix == ".traj" and "relaxation" in source.name:
            copied["relaxation_trajectory_file"] = str(target)
        elif source.name == "final_relaxed_structures.xyz":
            copied["final_relaxed_structures"] = str(target)
    return copied


@contextmanager
def capture_logs(log_path: Path) -> Iterator[io.StringIO]:
    """Capture stdout/stderr and duplicate AdsMind logger output into a file."""
    stream = io.StringIO()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    attached_loggers: List[logging.Logger] = []
    logger_map = logging.root.manager.loggerDict
    for name, logger_obj in logger_map.items():
        if not isinstance(logger_obj, logging.Logger):
            continue
        if name.startswith("adsmind.") or name.startswith("research."):
            logger_obj.addHandler(file_handler)
            attached_loggers.append(logger_obj)

    try:
        with redirect_stdout(stream), redirect_stderr(stream):
            yield stream
    finally:
        with log_path.open("a", encoding="utf-8") as handle:
            text = stream.getvalue()
            if text:
                handle.write(text)
        for logger_obj in attached_loggers:
            logger_obj.removeHandler(file_handler)
        file_handler.close()


class DryRunExecutor:
    """Deterministic executor used by tests and smoke runs."""

    def invoke(self, initial_state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session_dir = ensure_output_dir(initial_state["session_id"])
        best_file = session_dir / "BEST_dry_run_bridge_E-1.234.xyz"
        gen_file = session_dir / "generated_conformers_dry_run.traj"
        traj_file = session_dir / "relaxation_run.traj"
        final_xyz = session_dir / "final_relaxed_structures.xyz"
        best_file.write_text(
            "3\nDry-run adsorption structure\n"
            "Pt 0.0 0.0 0.0\n"
            "Pt 2.7 0.0 0.0\n"
            "H 1.35 0.0 1.05\n",
            encoding="utf-8",
        )
        final_xyz.write_text(best_file.read_text(encoding="utf-8"), encoding="utf-8")
        for path in (gen_file, traj_file):
            path.write_text("dry-run artifact\n", encoding="utf-8")
        (session_dir / "summary_report.md").write_text(
            "# AdsMind Summarizer Report\n\nDry-run final report.\n",
            encoding="utf-8",
        )
        (session_dir / "best_configuration.png").write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                "1f15c4890000000a49444154789c636000000200015f15c48900000000"
                "49454e44ae426082"
            )
        )
        (session_dir / "iteration_energy_curve.png").write_bytes(
            (session_dir / "best_configuration.png").read_bytes()
        )

        analysis = {
            "status": "success",
            "most_stable_energy_eV": -1.234,
            "bond_change_count": 0,
            "is_dissociated": False,
            "best_structure_file": str(best_file),
            "generated_conformers_file": str(gen_file),
            "relaxation_trajectory_file": str(traj_file),
            "site_analysis": {
                "planned_site_type": "bridge",
                "actual_site_type": "bridge",
                "is_chemical_slip": False,
                "planned_symbols": ["Pt", "Pt"],
                "actual_symbols": ["Pt", "Pt"],
                "site_fingerprint": "Pt1-Pt2",
            },
        }
        plan = {
            "adsorbate_type": "ReactiveSpecies",
            "solution": {
                "action": "continue",
                "site_type": "bridge",
                "surface_binding_atoms": ["Pt", "Pt"],
                "adsorbate_binding_indices": [0],
                "relax_top_n": 1,
            },
        }
        attempt_record = {
            "attempt_index": 1,
            "plan_key": "bridge|Pt,Pt|0|ReactiveSpecies|2.0",
            "status": "success",
            "most_stable_energy_eV": -1.234,
            "bond_change_count": 0,
            "is_dissociated": False,
            "is_chemical_slip": False,
            "planned_site_type": "bridge",
            "actual_site_type": "bridge",
            "best_structure_file": str(best_file),
            "generated_conformers_file": str(gen_file),
            "relaxation_trajectory_file": str(traj_file),
            "message": None,
            "history_entry": "【✅ Perfect Adsorption】 bridge @ ['Pt', 'Pt'] (Index [0]) -> Site: bridge (Pt,Pt) [🌟 New Best] | E=-1.234 eV",
        }
        final_state = dict(initial_state)
        final_state.update(
            {
                "plan": plan,
                "analysis_json": json.dumps(analysis),
                "history": [attempt_record["history_entry"]],
                "attempt_records": [attempt_record],
                "best_result": {
                    "most_stable_energy_eV": -1.234,
                    "analysis_json": analysis,
                    "plan": plan,
                    "result_type": "Perfect",
                },
                "best_dissociated_result": None,
                "total_input_tokens": 111,
                "total_output_tokens": 57,
                "messages": [AIMessage(content="Dry-run final report")],
                "summary_report_file": str(session_dir / "summary_report.md"),
                "best_configuration_png": str(session_dir / "best_configuration.png"),
                "iteration_energy_curve_png": str(session_dir / "iteration_energy_curve.png"),
                "visualization_error": None,
            }
        )
        return final_state


def summarize_directory(output_dir: Path | str) -> List[Dict[str, Any]]:
    """Scan a run directory and return flattened summary rows."""
    output_path = resolve_repo_path(output_dir)
    if not output_path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for case_dir in sorted(output_path.iterdir()):
        result_path = case_dir / DEFAULT_RESULT_NAME
        if not case_dir.is_dir() or not result_path.exists():
            continue
        with result_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows.append(summary_row_from_result(payload))
    return rows


def write_summary_csv(rows: Sequence[Dict[str, Any]], output_path: Path | str) -> Path:
    """Write summary rows to disk with a fixed column order."""
    output = resolve_repo_path(output_path)
    identity = identity_from_path(output)
    metadata = summary_metadata(identity) if identity is not None else {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for row in rows:
            enriched_row = {**metadata, **row}
            writer.writerow({column: enriched_row.get(column, "") for column in SUMMARY_COLUMNS})
    return output


def normalise_case_ids(case_ids: str | Iterable[str]) -> List[str]:
    """Normalize case ids to zero-padded strings."""
    if isinstance(case_ids, str):
        raw_items = [item.strip() for item in case_ids.split(",") if item.strip()]
    else:
        raw_items = [str(item).strip() for item in case_ids if str(item).strip()]
    return [item.zfill(2) for item in raw_items]


def rank_biserial_from_differences(differences: Sequence[float]) -> Optional[float]:
    """Compute the rank-biserial correlation for paired differences."""
    non_zero = [value for value in differences if value != 0]
    if not non_zero:
        return None
    ranks = rankdata([abs(value) for value in non_zero])
    positive = sum(rank for rank, value in zip(ranks, non_zero) if value > 0)
    negative = sum(rank for rank, value in zip(ranks, non_zero) if value < 0)
    total = positive + negative
    if total == 0:
        return None
    return (positive - negative) / total


def benjamini_hochberg(p_values: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """Apply BH-FDR correction without adding a hard dependency on statsmodels."""
    filtered = [(name, value) for name, value in p_values.items() if value is not None]
    if not filtered:
        return {name: None for name in p_values}

    filtered.sort(key=lambda item: item[1])
    total = len(filtered)
    adjusted: Dict[str, float] = {}
    running_min = 1.0
    for index, (name, value) in enumerate(reversed(filtered), start=1):
        rank = total - index + 1
        adjusted_value = min(running_min, value * total / rank)
        running_min = adjusted_value
        adjusted[name] = adjusted_value

    return {name: adjusted.get(name) for name in p_values}


def compute_bootstrap_ci(values: Sequence[float]) -> Optional[Dict[str, float]]:
    """Bootstrap the median with a 95% CI."""
    if len(values) < 2:
        return None
    result = bootstrap(
        (list(values),),
        statistic=median,
        confidence_level=0.95,
        n_resamples=5000,
        method="basic",
        random_state=42,
    )
    return {
        "low": float(result.confidence_interval.low),
        "high": float(result.confidence_interval.high),
    }


def exact_mcnemar(success_pairs: Sequence[tuple[bool, bool]]) -> Optional[Dict[str, float]]:
    """Run exact McNemar via the binomial test on discordant pairs."""
    b = 0
    c = 0
    for left, right in success_pairs:
        if left and not right:
            b += 1
        elif right and not left:
            c += 1
    if b + c == 0:
        return None
    test = binomtest(min(b, c), n=b + c, p=0.5)
    return {"b": b, "c": c, "p_value": float(test.pvalue)}


def failure_payload(exc: BaseException) -> Dict[str, Any]:
    """Return a stable failure payload for logging/serialization."""
    return {
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }
