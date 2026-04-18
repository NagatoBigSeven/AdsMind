"""Run a high-symmetry-site non-LLM adsorption baseline."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import List, Optional

from ase.io import read
from autoadsorbate import Surface

from research.agent_eval.baseline_utils import (
    CandidateRecord,
    adsorbate_reference_energy,
    adsorbate_type_for_smiles,
    build_adsorbate_from_smiles,
    choose_binding_indices,
    init_mace_calculator,
    normalise_case_ids,
    relax_candidate,
    summarize_candidate_records,
    surface_reference_energy,
    write_csv,
    write_json,
)
from research.agent_eval.common import load_manifest_map, resolve_repo_path
from src.tools.fragment import (
    _bump_adsorbate_to_safe_distance,
    create_fragment_from_plan,
)
from src.tools.patches import apply_autoadsorbate_patches


SUMMARY_FIELDS = [
    "case_id",
    "n_sites",
    "status",
    "successful",
    "failed",
    "best_energy",
    "mean_energy",
    "std_energy",
    "best_structure_file",
    "wall_clock_sec",
]


def site_type_from_connectivity(connectivity: int) -> str:
    """Map AutoAdsorbate connectivity to canonical site type."""
    if int(connectivity) == 1:
        return "ontop"
    if int(connectivity) == 2:
        return "bridge"
    return "hollow"


def site_formula_symbols(site_formula) -> List[str]:
    """Expand AutoAdsorbate site_formula dictionaries to a sorted symbol list."""
    if not isinstance(site_formula, dict):
        return []
    symbols: List[str] = []
    for symbol, count in site_formula.items():
        symbols.extend([str(symbol)] * int(count))
    return sorted(symbols)


def build_site_fragment(smiles: str, site_type: str, conformers: int):
    """Create the deterministic fragment for one site type."""
    binding_indices = choose_binding_indices(smiles, site_type)
    plan = {
        "adsorbate_type": adsorbate_type_for_smiles(smiles),
        "solution": {
            "site_type": site_type,
            "adsorbate_binding_indices": binding_indices,
        },
    }
    return create_fragment_from_plan(
        original_smiles=smiles,
        binding_atom_indices=binding_indices,
        plan_dict=plan,
        to_initialize=conformers,
    )


def generate_site_systems(
    *,
    slab,
    smiles: str,
    site_index,
    site_type: str,
    conformers_per_site: int,
):
    """Generate initial structures for one exact AutoAdsorbate site."""
    clean_slab = slab.copy()
    surface = Surface(clean_slab, precision=1.0, touch_sphere_size=2.0, mode="slab")
    surface.site_df = surface.site_df.loc[[site_index]]
    fragment = build_site_fragment(smiles, site_type, conformers_per_site)
    sample_rotation = len(fragment.info["plan_binding_atom_indices"]) != 2
    raw = surface.get_populated_sites(
        fragment=fragment,
        site_index=[site_index],
        sample_rotation=sample_rotation,
        mode="all",
        conformers_per_site_cap=conformers_per_site,
        overlap_thr=0.1,
        verbose=False,
    )
    systems = []
    for atoms in raw:
        if site_type in {"bridge", "hollow"}:
            atoms.positions[len(slab):, 2] += 0.8
        systems.append(_bump_adsorbate_to_safe_distance(slab, atoms))
    return systems


def run_case(
    *,
    case_row,
    output_root: Path,
    calc,
    fmax: float,
    steps: int,
    conformers_per_site: int,
):
    """Run one high-symmetry-site case."""
    started = time.perf_counter()
    case_id = case_row["case_id"]
    case_dir = output_root / case_id
    slab = read(str(resolve_repo_path(case_row["slab_file"])))
    adsorbate = build_adsorbate_from_smiles(case_row["smiles"])
    e_surface = surface_reference_energy(slab, calc)
    e_adsorbate = adsorbate_reference_energy(adsorbate, calc, fmax=fmax, steps=steps)

    surface = Surface(slab.copy(), precision=1.0, touch_sphere_size=2.0, mode="slab")
    sites = surface.site_df.copy()
    records = []
    for count, (site_index, site_row) in enumerate(sites.iterrows(), start=1):
        site_type = site_type_from_connectivity(site_row.get("connectivity", 0))
        site_symbols = site_formula_symbols(site_row.get("site_formula"))
        label = f"{site_type}_{int(site_index):03d}"
        try:
            systems = generate_site_systems(
                slab=slab,
                smiles=case_row["smiles"],
                site_index=site_index,
                site_type=site_type,
                conformers_per_site=conformers_per_site,
            )
        except Exception as exc:
            records.append(
                CandidateRecord(
                    label=label,
                    status="error",
                    error=f"{type(exc).__name__}: {exc}",
                    metadata={
                        "site_index": int(site_index),
                        "site_type": site_type,
                        "site_symbols": site_symbols,
                        "placement_error": f"{type(exc).__name__}: {exc}",
                    },
                )
            )
            print(f"[heuristic] case={case_id} site={count}/{len(sites)} placement failed", flush=True)
            continue

        for conf_index, system in enumerate(systems):
            candidate_label = f"{label}_conf{conf_index}"
            records.append(
                relax_candidate(
                    label=candidate_label,
                    system=system,
                    slab=slab,
                    calc=calc,
                    e_surface=e_surface,
                    e_adsorbate=e_adsorbate,
                    fmax=fmax,
                    steps=steps,
                    metadata={
                        "site_index": int(site_index),
                        "site_type": site_type,
                        "site_symbols": site_symbols,
                        "conformer_index": conf_index,
                    },
                )
            )
            latest = records[-1]
            if latest.status == "success":
                print(
                    f"[heuristic] case={case_id} site={count}/{len(sites)} "
                    f"E_ads={latest.adsorption_energy_eV:.6f}",
                    flush=True,
                )
            else:
                print(f"[heuristic] case={case_id} site={count}/{len(sites)} failed", flush=True)

    summary = summarize_candidate_records(
        records=records,
        output_dir=case_dir,
        structure_prefix=f"{case_id}_heuristic",
        top_n=3,
    )
    summary.update(
        {
            "case_id": case_id,
            "n_sites": int(len(sites)),
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
    parser.add_argument("--output", required=True)
    parser.add_argument("--fmax", type=float, default=0.10)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--conformers-per-site", type=int, default=1)
    args = parser.parse_args(argv)

    apply_autoadsorbate_patches()
    manifest = load_manifest_map(args.manifest)
    output_root = resolve_repo_path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    calc = init_mace_calculator(model="small", device="cpu", dtype="float32")

    rows = []
    summaries = []
    for case_id in normalise_case_ids(args.cases):
        summary = run_case(
            case_row=manifest[case_id],
            output_root=output_root,
            calc=calc,
            fmax=args.fmax,
            steps=args.steps,
            conformers_per_site=args.conformers_per_site,
        )
        summaries.append(summary)
        rows.append(
            {
                "case_id": case_id,
                "n_sites": summary["n_sites"],
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
