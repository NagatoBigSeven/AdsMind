"""Run a random-placement non-LLM adsorption baseline."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
from ase.io import read

from research.agent_eval.baseline_utils import (
    adsorbate_reference_energy,
    build_adsorbate_from_smiles,
    init_mace_calculator,
    normalise_case_ids,
    relax_candidate,
    summarize_candidate_records,
    surface_reference_energy,
    write_csv,
    write_json,
)
from research.agent_eval.common import load_manifest_map, resolve_repo_path

try:
    from scipy.spatial.transform import Rotation
except Exception:  # pragma: no cover - scipy is part of the experiment env.
    Rotation = None


SUMMARY_FIELDS = [
    "case_id",
    "n_random",
    "status",
    "successful",
    "failed",
    "best_energy",
    "mean_energy",
    "std_energy",
    "best_structure_file",
    "wall_clock_sec",
]


def random_rotation_matrix(rng: np.random.Generator) -> np.ndarray:
    """Return a random 3x3 rotation matrix."""
    if Rotation is not None:
        return Rotation.random(random_state=rng).as_matrix()
    matrix = rng.normal(size=(3, 3))
    q_matrix, r_matrix = np.linalg.qr(matrix)
    return q_matrix @ np.diag(np.sign(np.diag(r_matrix)))


def place_random_adsorbate(slab, adsorbate, rng: np.random.Generator):
    """Place one adsorbate at a random xy cell position above the slab."""
    ads = adsorbate.copy()
    centered = ads.positions - ads.get_center_of_mass()
    ads.positions = centered @ random_rotation_matrix(rng).T

    frac_xy = rng.random(2)
    xy_vec = frac_xy[0] * slab.cell[0] + frac_xy[1] * slab.cell[1]
    z = float(slab.positions[:, 2].max()) + 2.0
    ads.positions += [float(xy_vec[0]), float(xy_vec[1]), z]
    system = slab.copy() + ads
    system.set_cell(slab.cell)
    system.set_pbc(slab.pbc)
    return system, {"frac_x": float(frac_xy[0]), "frac_y": float(frac_xy[1]), "z_A": z}


def run_case(
    *,
    case_row,
    n_random: int,
    output_root: Path,
    calc,
    fmax: float,
    steps: int,
    seed: int,
):
    """Run one random-placement case."""
    started = time.perf_counter()
    case_id = case_row["case_id"]
    case_dir = output_root / case_id
    slab = read(str(resolve_repo_path(case_row["slab_file"])))
    adsorbate = build_adsorbate_from_smiles(case_row["smiles"], seed=seed)
    e_surface = surface_reference_energy(slab, calc)
    e_adsorbate = adsorbate_reference_energy(adsorbate, calc, fmax=fmax, steps=steps)
    rng = np.random.default_rng(seed + int(case_id))

    records = []
    for index in range(n_random):
        label = f"random_{index:03d}"
        system, placement_meta = place_random_adsorbate(slab, adsorbate, rng)
        records.append(
            relax_candidate(
                label=label,
                system=system,
                slab=slab,
                calc=calc,
                e_surface=e_surface,
                e_adsorbate=e_adsorbate,
                fmax=fmax,
                steps=steps,
                metadata=placement_meta,
            )
        )
        latest = records[-1]
        if latest.status == "success":
            print(
                f"[random] case={case_id} {index + 1}/{n_random} "
                f"E_ads={latest.adsorption_energy_eV:.6f}",
                flush=True,
            )
        else:
            print(f"[random] case={case_id} {index + 1}/{n_random} failed", flush=True)

    summary = summarize_candidate_records(
        records=records,
        output_dir=case_dir,
        structure_prefix=f"{case_id}_random",
        top_n=3,
    )
    summary.update(
        {
            "case_id": case_id,
            "n_random": n_random,
            "slab_file": case_row["slab_file"],
            "smiles": case_row["smiles"],
            "surface_reference_eV": e_surface,
            "adsorbate_reference_eV": e_adsorbate,
            "wall_clock_sec": time.perf_counter() - started,
        }
    )
    write_json(case_dir / "result.json", summary)
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--n-random", type=int, default=20)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fmax", type=float, default=0.10)
    parser.add_argument("--steps", type=int, default=200)
    args = parser.parse_args(argv)

    manifest = load_manifest_map(args.manifest)
    output_root = resolve_repo_path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    calc = init_mace_calculator(model="small", device="cpu", dtype="float32")

    rows = []
    summaries = []
    for case_id in normalise_case_ids(args.cases):
        summary = run_case(
            case_row=manifest[case_id],
            n_random=args.n_random,
            output_root=output_root,
            calc=calc,
            fmax=args.fmax,
            steps=args.steps,
            seed=args.seed,
        )
        summaries.append(summary)
        rows.append(
            {
                "case_id": case_id,
                "n_random": args.n_random,
                "status": summary["status"],
                "successful": summary["successful"],
                "failed": summary["failed"],
                "best_energy": summary["best_energy_eV"],
                "mean_energy": summary["mean_energy_eV"],
                "std_energy": summary["std_energy_eV"],
                "best_structure_file": summary["best_structure_file"],
                "wall_clock_sec": summary["wall_clock_sec"],
            }
        )

    write_csv(output_root / "summary.csv", rows, SUMMARY_FIELDS)
    write_json(output_root / "summary.json", {"cases": summaries})
    print(output_root / "summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
