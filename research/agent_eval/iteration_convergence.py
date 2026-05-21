"""Extract per-iteration running-best energies from AdsMind result files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from research.agent_eval.experiment_identity import identity_from_path, summary_metadata


ROOT = Path(__file__).resolve().parents[2]


def resolve_repo_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def backend_label(path: Path) -> str:
    """Return the reproducible backend directory name for a run path."""
    identity = identity_from_path(path)
    return identity.result_dir if identity is not None else path.name


def extract_convergence(result_json_path: Path) -> List[Optional[float]]:
    """Extract running-best energy at each iteration."""
    with result_json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    records = data.get("attempt_records", [])
    running_best: List[Optional[float]] = []
    best_so_far = float("inf")
    for rec in records:
        energy = rec.get("most_stable_energy_eV")
        if energy is not None and is_valid_adsorption_attempt(rec):
            best_so_far = min(best_so_far, float(energy))
        running_best.append(None if best_so_far == float("inf") else best_so_far)
    return running_best


def is_valid_adsorption_attempt(record: Dict[str, Any]) -> bool:
    """Return True only for successful, non-dissociated adsorption attempts."""
    if record.get("status") != "success":
        return False
    if record.get("is_dissociated"):
        return False
    history = str(record.get("history_entry") or "")
    return "Dissociated" not in history


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(rows: List[Dict[str, Any]], max_iters: int) -> Dict[str, Any]:
    """Summarize mean curves and early-improvement fractions by backend."""
    payload: Dict[str, Any] = {"backends": {}}
    for backend in sorted({row["backend"] for row in rows}):
        backend_rows = [row for row in rows if row["backend"] == backend]
        curves = []
        for row in backend_rows:
            curves.append([row.get(f"iter_{idx}") for idx in range(1, max_iters + 1)])
        mean_curve = []
        for idx in range(max_iters):
            values = [curve[idx] for curve in curves if curve[idx] not in {"", None}]
            mean_curve.append(float(np.mean([float(value) for value in values])) if values else None)

        fractions: Dict[str, List[float]] = {"iter_2": [], "iter_3": []}
        for row in backend_rows:
            first = row.get("iter_1")
            final = row.get("final_best")
            if first in {"", None} or final in {"", None}:
                continue
            first_f = float(first)
            final_f = float(final)
            denom = first_f - final_f
            if abs(denom) < 1e-12:
                fractions["iter_2"].append(1.0)
                fractions["iter_3"].append(1.0)
                continue
            for iter_key in fractions:
                value = row.get(iter_key)
                if value in {"", None}:
                    continue
                fractions[iter_key].append((first_f - float(value)) / denom)

        payload["backends"][backend] = {
            "num_cases": len(backend_rows),
            "num_success": sum(1 for row in backend_rows if row.get("final_best") not in {"", None}),
            "mean_running_best": mean_curve,
            "mean_fraction_of_final_improvement_by_iter2": (
                float(np.mean(fractions["iter_2"])) if fractions["iter_2"] else None
            ),
            "mean_fraction_of_final_improvement_by_iter3": (
                float(np.mean(fractions["iter_3"])) if fractions["iter_3"] else None
            ),
        }
    return payload


def maybe_plot(summary: Dict[str, Any], output_csv: Path) -> Optional[Path]:
    """Write a convergence plot when matplotlib is available."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    plot_path = output_csv.with_suffix(".png")
    for backend, data in summary["backends"].items():
        curve = data["mean_running_best"]
        xs = list(range(1, len(curve) + 1))
        ys = [np.nan if value is None else value for value in curve]
        plt.plot(xs, ys, marker="o", label=backend)
    plt.xlabel("Iteration")
    plt.ylabel("Mean running-best adsorption energy (eV)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=200)
    plt.close()
    return plot_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ablation-dirs", required=True)
    parser.add_argument("--variant", default="full")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    rows: List[Dict[str, Any]] = []
    max_iters = 0
    for raw_dir in [item.strip() for item in args.ablation_dirs.split(",") if item.strip()]:
        ablation_dir = resolve_repo_path(raw_dir)
        variant_dir = ablation_dir / args.variant
        if not variant_dir.exists():
            continue
        label = backend_label(ablation_dir)
        for result_path in sorted(variant_dir.glob("*/result.json")):
            case_id = result_path.parent.name.zfill(2)
            curve = extract_convergence(result_path)
            max_iters = max(max_iters, len(curve))
            identity = identity_from_path(ablation_dir)
            row: Dict[str, Any] = {"case_id": case_id}
            if identity is not None:
                row.update(summary_metadata(identity))
            else:
                row["backend"] = label
            for idx, energy in enumerate(curve, start=1):
                row[f"iter_{idx}"] = energy
            row["final_best"] = next((energy for energy in reversed(curve) if energy is not None), None)
            rows.append(row)

    fieldnames = [
        "case_id",
        "backend_key",
        "backend",
        "llm_model",
        "force_field",
        "calculator_backend",
        "force_field_model",
        "force_field_size",
    ] + [f"iter_{idx}" for idx in range(1, max_iters + 1)] + ["final_best"]
    for row in rows:
        for field in fieldnames:
            row.setdefault(field, "")
    output = resolve_repo_path(args.output)
    write_csv(output, rows, fieldnames)
    summary = summarize(rows, max_iters)
    summary_path = output.with_name(output.stem + "_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    plot_path = maybe_plot(summary, output)
    print(output)
    print(summary_path)
    if plot_path is not None:
        print(plot_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
