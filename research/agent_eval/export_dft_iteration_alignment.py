"""Export per-iteration AdsMind trajectories for DFT alignment.

The output is intentionally lightweight: it copies the already saved XYZ
structures and writes CSV/Markdown metadata.  It does not require ASE, because
the immediate goal is to hand trajectories to DFT collaborators and compare
against their optimized reference structures later.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_RUNS = [
    ("Gemini_2.5_Pro", "research/results/gemini_ablation_v1/full"),
    ("GPT_5.4", "research/results/openai_gpt54_ablation_v1/full"),
    ("Claude_Sonnet_4.6", "research/results/anthropic_sonnet46_ablation_v1/full"),
    ("Grok_4", "research/results/xai_ablation_v2/full"),
]


TRAJECTORY_FIELDS = [
    "case_id",
    "backend",
    "variant",
    "run_dir",
    "run_status",
    "run_best_energy_eV",
    "iteration_count",
    "attempt_index",
    "attempt_status",
    "action",
    "planner_reasoning",
    "planner_solution_json",
    "planned_motif_summary",
    "planned_site_type",
    "planned_surface_binding_atoms",
    "planned_adsorbate_binding_indices",
    "actual_site_type",
    "actual_surface_binding_atoms",
    "mace_energy_eV",
    "delta_from_run_best_eV",
    "is_run_best_iteration",
    "is_chemical_slip",
    "is_dissociated",
    "bond_change_count",
    "history_entry",
    "source_structure",
    "copied_structure",
]


ENERGY_FIELDS = [
    "case_id",
    "backend",
    "variant",
    "attempt_index",
    "mace_energy_eV",
    "delta_from_run_best_eV",
    "is_run_best_iteration",
    "attempt_status",
    "planned_site_type",
    "actual_site_type",
    "is_chemical_slip",
    "is_dissociated",
]


SUMMARY_FIELDS = [
    "case_id",
    "backend",
    "variant",
    "run_status",
    "iteration_count",
    "successful_attempts",
    "best_iteration",
    "first_success_energy_eV",
    "best_energy_eV",
    "improvement_vs_first_eV",
    "chemical_slip_count",
    "dissociation_count",
    "final_actual_site_type",
    "best_structure",
]


DFT_TEMPLATE_FIELDS = [
    "case_id",
    "dft_label",
    "reference_role",
    "structure_file",
    "functional",
    "encut_eV",
    "kpoints",
    "E_slab_eV",
    "E_adsorbate_eV",
    "E_slab_ads_eV",
    "E_ads_eV",
    "G_correction_eV",
    "Delta_G_eV",
    "snapshot_file",
    "notes",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_path(raw: str | Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return repo_root() / p


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def clean_slug(value: Any, max_len: int = 80) -> str:
    text = str(value if value is not None else "NA")
    text = re.sub(r"[^0-9A-Za-z_.-]+", "_", text).strip("_")
    return (text[:max_len] or "NA").strip("_")


def parse_actual_atoms(message: str) -> str:
    match = re.search(r"Actual \[(.*?)\]", message or "")
    if not match:
        return ""
    atoms = [item.strip().strip("'\"") for item in match.group(1).split(",") if item.strip()]
    return ";".join(atoms)


def as_semicolon_list(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ";".join(str(item) for item in value)
    return str(value)


def compact_json(value: Any) -> str:
    if value in ("", None):
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def motif_summary(solution: Dict[str, Any]) -> str:
    site = solution.get("site_type", "")
    surface = as_semicolon_list(solution.get("surface_binding_atoms"))
    ads = as_semicolon_list(solution.get("adsorbate_binding_indices"))
    bits = []
    if site:
        bits.append(str(site))
    if surface:
        bits.append(f"surface={surface}")
    if ads:
        bits.append(f"adsorbate_idx={ads}")
    return " | ".join(bits)


def resolve_artifact(result_dir: Path, result: Dict[str, Any], raw_path: str) -> Optional[Path]:
    if not raw_path:
        return None
    direct = resolve_path(raw_path)
    if direct.exists():
        return direct
    basename = Path(raw_path).name
    artifacts = result.get("artifact_paths", {})
    for value in artifacts.values():
        candidate = resolve_path(value)
        if candidate.name == basename and candidate.exists():
            return candidate
    fallback = result_dir / "artifacts" / basename
    if fallback.exists():
        return fallback
    return None


def copy_structure(source: Optional[Path], target_dir: Path, label: str) -> str:
    if source is None or not source.exists():
        return ""
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix or ".xyz"
    target = target_dir / f"{clean_slug(label)}{suffix}"
    shutil.copy2(source, target)
    return str(target)


def collect_run(case_id: str, backend: str, run_dir_raw: str, output_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    run_dir = resolve_path(run_dir_raw)
    result_dir = run_dir / case_id
    result_path = result_dir / "result.json"
    if not result_path.exists():
        summary = {
            "case_id": case_id,
            "backend": backend,
            "variant": "full",
            "run_status": "missing",
        }
        return [], summary

    result = load_json(result_path)
    run_best = result.get("best_energy_eV")
    try:
        run_best_float = float(run_best)
    except (TypeError, ValueError):
        run_best_float = None

    rows: List[Dict[str, Any]] = []
    successful: List[Dict[str, Any]] = []
    structures_dir = output_dir / "structures" / clean_slug(backend)
    for record in result.get("attempt_records", []):
        solution = record.get("plan", {}).get("solution", {})
        energy = record.get("most_stable_energy_eV")
        try:
            energy_float = float(energy)
        except (TypeError, ValueError):
            energy_float = None

        source = resolve_artifact(result_dir, result, record.get("best_structure_file", ""))
        attempt_index = record.get("attempt_index", "")
        actual_site = record.get("actual_site_type", "")
        planned_site = record.get("planned_site_type") or solution.get("site_type", "")
        label = (
            f"iter{int(attempt_index):02d}_E{energy_float:.6f}_{planned_site}_to_{actual_site}"
            if isinstance(attempt_index, int) and energy_float is not None
            else f"iter{attempt_index}_{planned_site}_to_{actual_site}"
        )
        copied = copy_structure(source, structures_dir, label)
        delta = ""
        if energy_float is not None and run_best_float is not None:
            delta = energy_float - run_best_float
        is_best = bool(energy_float is not None and run_best_float is not None and abs(energy_float - run_best_float) < 1e-9)

        row = {
            "case_id": case_id,
            "backend": backend,
            "variant": "full",
            "run_dir": str(run_dir),
            "run_status": result.get("status", ""),
            "run_best_energy_eV": run_best,
            "iteration_count": result.get("iteration_count", ""),
            "attempt_index": attempt_index,
            "attempt_status": record.get("status", ""),
            "action": solution.get("action", ""),
            "planner_reasoning": record.get("plan", {}).get("reasoning", ""),
            "planner_solution_json": compact_json(solution),
            "planned_motif_summary": motif_summary(solution),
            "planned_site_type": planned_site,
            "planned_surface_binding_atoms": as_semicolon_list(solution.get("surface_binding_atoms")),
            "planned_adsorbate_binding_indices": as_semicolon_list(solution.get("adsorbate_binding_indices")),
            "actual_site_type": actual_site,
            "actual_surface_binding_atoms": parse_actual_atoms(record.get("message", "")),
            "mace_energy_eV": energy,
            "delta_from_run_best_eV": delta,
            "is_run_best_iteration": is_best,
            "is_chemical_slip": record.get("is_chemical_slip", ""),
            "is_dissociated": record.get("is_dissociated", ""),
            "bond_change_count": record.get("bond_change_count", ""),
            "history_entry": record.get("history_entry", ""),
            "source_structure": str(source) if source else "",
            "copied_structure": copied,
        }
        rows.append(row)
        if record.get("status") == "success" and energy_float is not None:
            successful.append(row)

    successful.sort(key=lambda item: float(item["mace_energy_eV"]))
    best_row = successful[0] if successful else {}
    first_energy = ""
    if rows:
        for row in rows:
            if row.get("mace_energy_eV") not in ("", None):
                first_energy = row["mace_energy_eV"]
                break
    improvement = ""
    if first_energy not in ("", None) and best_row:
        improvement = float(first_energy) - float(best_row["mace_energy_eV"])

    summary = {
        "case_id": case_id,
        "backend": backend,
        "variant": "full",
        "run_status": result.get("status", ""),
        "iteration_count": result.get("iteration_count", ""),
        "successful_attempts": len(successful),
        "best_iteration": best_row.get("attempt_index", ""),
        "first_success_energy_eV": first_energy,
        "best_energy_eV": best_row.get("mace_energy_eV", ""),
        "improvement_vs_first_eV": improvement,
        "chemical_slip_count": result.get("chemical_slip_count", ""),
        "dissociation_count": result.get("dissociation_count", ""),
        "final_actual_site_type": result.get("final_site_type", ""),
        "best_structure": best_row.get("copied_structure", ""),
    }
    return rows, summary


def energy_rows_from_trajectory(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{field: row.get(field, "") for field in ENERGY_FIELDS} for row in rows]


def classify_summary(row: Dict[str, Any]) -> str:
    status = row.get("run_status")
    if status != "success":
        return "missing-or-failed-run"
    try:
        improvement = float(row.get("improvement_vs_first_eV", 0) or 0)
    except ValueError:
        improvement = 0.0
    try:
        best_iteration = int(row.get("best_iteration", 0) or 0)
    except ValueError:
        best_iteration = 0
    try:
        slip_count = int(row.get("chemical_slip_count", 0) or 0)
    except ValueError:
        slip_count = 0
    if improvement >= 0.02:
        return "reasoning-recovery-like"
    if best_iteration <= 1 and slip_count == 0:
        return "first-shot-close-and-stable"
    if improvement < 0.005:
        return "memory-like-with-degenerate-refinement"
    return "minor-feedback-refinement"


def write_energy_curve_svg(output_dir: Path, rows: List[Dict[str, Any]]) -> None:
    points_by_backend: Dict[str, List[Tuple[int, float, bool]]] = {}
    for row in rows:
        if row.get("mace_energy_eV") in ("", None):
            continue
        try:
            attempt = int(row.get("attempt_index"))
            energy = float(row.get("mace_energy_eV"))
        except (TypeError, ValueError):
            continue
        points_by_backend.setdefault(str(row.get("backend")), []).append(
            (attempt, energy, str(row.get("is_run_best_iteration")) == "True")
        )

    width, height = 920, 520
    left, right, top, bottom = 90, 230, 45, 80
    plot_w = width - left - right
    plot_h = height - top - bottom
    energies = [energy for points in points_by_backend.values() for _, energy, _ in points]
    attempts = [attempt for points in points_by_backend.values() for attempt, _, _ in points]
    if not energies or not attempts:
        return
    y_min, y_max = min(energies), max(energies)
    pad = max((y_max - y_min) * 0.12, 0.005)
    y_min -= pad
    y_max += pad
    x_min, x_max = 1, max(attempts)
    if x_max == x_min:
        x_max += 1

    def x(attempt: int) -> float:
        return left + (attempt - x_min) / (x_max - x_min) * plot_w

    def y(energy: float) -> float:
        return top + (y_max - energy) / (y_max - y_min) * plot_h

    colors = {
        "Gemini_2.5_Pro": "#1f77b4",
        "GPT_5.4": "#d62728",
        "Claude_Sonnet_4.6": "#9467bd",
        "Grok_4": "#2ca02c",
    }

    svg: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;font-size:15px}.small{font-size:12px}.title{font-size:20px;font-weight:bold}</style>',
        f'<text x="{left}" y="28" class="title">CMU case 01 AdsMind iteration energy trajectory</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#222" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#222" stroke-width="1.4"/>',
        f'<text x="{left + plot_w / 2 - 40}" y="{height - 25}">Attempt</text>',
        f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})">MACE adsorption energy (eV)</text>',
        f'<text x="{left}" y="{height - 8}" class="small">MACE-small trajectory only; DFT/PBE reference structure is not plotted as a MACE-energy point.</text>',
    ]
    for attempt in range(x_min, x_max + 1):
        xx = x(attempt)
        svg.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top + plot_h}" stroke="#eee"/>')
        svg.append(f'<text x="{xx - 4:.1f}" y="{top + plot_h + 24}">{attempt}</text>')
    for i in range(5):
        value = y_min + i * (y_max - y_min) / 4
        yy = y(value)
        svg.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="#eee"/>')
        svg.append(f'<text x="{left - 78}" y="{yy + 5:.1f}" class="small">{value:.3f}</text>')

    legend_y = top + 20
    for backend, points in points_by_backend.items():
        points = sorted(points)
        color = colors.get(backend, "#555")
        path = " ".join(f"{x(a):.1f},{y(e):.1f}" for a, e, _ in points)
        svg.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        for attempt, energy, is_best in points:
            radius = 6 if is_best else 4
            fill = color if is_best else "white"
            svg.append(
                f'<circle cx="{x(attempt):.1f}" cy="{y(energy):.1f}" r="{radius}" '
                f'fill="{fill}" stroke="{color}" stroke-width="2"/>'
            )
        svg.append(f'<line x1="{left + plot_w + 35}" y1="{legend_y}" x2="{left + plot_w + 62}" y2="{legend_y}" stroke="{color}" stroke-width="2.4"/>')
        svg.append(f'<circle cx="{left + plot_w + 48}" cy="{legend_y}" r="4" fill="{color}"/>')
        svg.append(f'<text x="{left + plot_w + 72}" y="{legend_y + 5}" class="small">{backend}</text>')
        legend_y += 26
    svg.append("</svg>")
    (output_dir / "energy_curve.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


def write_handoff(output_dir: Path, summaries: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> None:
    total_structures = sum(1 for row in rows if row.get("copied_structure"))
    total_snapshots = len(list((output_dir / "snapshots").glob("*/*.png"))) if (output_dir / "snapshots").exists() else 0
    missing_structure_backends = sorted(
        {
            str(row.get("backend"))
            for row in rows
            if row.get("attempt_status") == "success" and not row.get("copied_structure")
        }
    )
    lines = [
        "# Lou/Bowen MVP Handoff: CMU case 01",
        "",
        "System: `Mo3Pd_111_H` / CMU case 01.",
        "",
        "Use this package for a first figure discussion only. The DFT/PBE final structure from Bowen is still needed before manuscript-grade structural alignment can be claimed.",
        "",
        "## Files to use now",
        "",
        "- `agent_iteration_trajectory.csv`: complete per-attempt table, including planner JSON and analyzer diagnostics.",
        "- `energy_curve.csv`: compact plotting table for the MACE-small energy trajectory.",
        "- `energy_curve.svg`: quick visual draft of the agent-observed MACE energy curve.",
        "- `agent_run_summary.csv`: backend-level summary and trajectory classification inputs.",
        "- `structures/`: currently copied relaxed `.xyz` files where artifacts exist.",
        "- `snapshots/`: quick transparent PNG renders generated from available `.xyz` files, if present.",
        "- `snapshot_contact_sheet.png`: quick contact sheet for discussion, if present.",
        "- `FILE_MANIFEST.md`: generated file list for handoff auditing, if present.",
        "- `dft_reference_template.csv`: values transcribed from Bowen's current `VASP.xls` column B plus fields still needed.",
        "",
        "## Provisional trajectory pattern before DFT structural alignment",
        "",
        "These labels are internal reading aids based only on the AdsMind/MACE trajectory. They should not be used as manuscript conclusions until Bowen's DFT/PBE final structure has been aligned.",
        "",
    ]
    for row in summaries:
        lines.append(
            f"- {row.get('backend')}: {classify_summary(row)}; "
            f"iterations={row.get('iteration_count')}, best iteration={row.get('best_iteration')}, "
            f"best MACE E={row.get('best_energy_eV')} eV, improvement vs first={row.get('improvement_vs_first_eV')} eV."
        )
    lines.extend(
        [
            "",
            "## Structure artifact status",
            "",
            f"- Copied relaxed structures available now: {total_structures}.",
            f"- Quick PNG snapshots available now: {total_snapshots}.",
            f"- Backends with successful metadata but missing local `.xyz` artifacts: {', '.join(missing_structure_backends) if missing_structure_backends else 'none'}.",
            "",
            "## Figure cautions",
            "",
            "- Plot MACE energy as the agent-observed trajectory.",
            "- Show Bowen's DFT/PBE final structure as a reference endpoint, not as a MACE-energy point.",
            "- Keep failed, worse, or slipped iterations in the table even if the figure only labels selected frames.",
            "- Do not call any AdsMind intermediate a transition state unless Bowen supplies a formal DFT TS/NEB result.",
        ]
    )
    (output_dir / "MVP_HANDOFF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_dft_template(output_dir: Path, case_id: str, overwrite: bool = False) -> None:
    template_path = output_dir / "dft_reference_template.csv"
    if template_path.exists() and not overwrite:
        return
    rows = [
        {
            "case_id": case_id,
            "dft_label": "Mo3Pd_111_H",
            "reference_role": "DFT optimized final state",
            "functional": "PBE",
            "E_slab_eV": "-568.24731439",
            "E_adsorbate_eV": "-3.361475545",
            "E_slab_ads_eV": "-572.73088949",
            "E_ads_eV": "-1.122099555",
            "G_correction_eV": "",
            "Delta_G_eV": "-0.988283055",
            "notes": "Values transcribed from VASP.xls column B; structure file and settings still needed from collaborator.",
        },
        {
            "case_id": case_id,
            "dft_label": "Mo3Pd_111_H_initial",
            "reference_role": "DFT initial modeled structure",
            "notes": "Needed for Panel D/E snapshots and geometry migration comparison.",
        },
        {
            "case_id": case_id,
            "dft_label": "Mo3Pd_111_H_TS_if_available",
            "reference_role": "transition state, only if explicitly optimized",
            "notes": "Do not use agent intermediate structures as TS unless DFT TS/NEB is provided.",
        },
    ]
    write_csv(template_path, rows, DFT_TEMPLATE_FIELDS)


def write_file_manifest(output_dir: Path) -> None:
    lines = [
        "# Case 01 DFT Alignment File Manifest",
        "",
        "All paths are relative to this directory.",
        "",
    ]
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "FILE_MANIFEST.md":
            continue
        rel = path.relative_to(output_dir)
        lines.append(f"- `{rel}` ({path.stat().st_size:,} bytes)")
    (output_dir / "FILE_MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(output_dir: Path, case_id: str, summaries: List[Dict[str, Any]]) -> None:
    lines = [
        f"# DFT iteration alignment prep: CMU case {case_id}",
        "",
        "Purpose: prepare AdsMind per-iteration trajectories for comparison against a DFT/PBE reference final state.",
        "",
        "Important interpretation rules:",
        "- Compare geometry/site migration first; do not directly equate MACE adsorption energies with VASP/PBE energies.",
        "- Treat DFT/PBE final state as the reference geometry once the collaborator provides the optimized structure.",
        "- Only call a structure TS if the collaborator provides a DFT transition-state/NEB result.",
        "",
        "Files:",
        "- `agent_iteration_trajectory.csv`: one row per AdsMind attempt.",
        "- `agent_run_summary.csv`: one row per backend full run.",
        "- `energy_curve.csv`: compact plotting table for the MACE-small trajectory.",
        "- `energy_curve.svg`: quick energy-curve draft for discussion.",
        "- `dft_reference_template.csv`: fields needed from the DFT side.",
        "- `structures/`: copied XYZ structures for every successful iteration with saved artifacts.",
        "- `snapshots/`: quick transparent PNG renders generated by `render_dft_alignment_snapshots.py`, if present.",
        "- `FILE_MANIFEST.md`: generated file list for handoff auditing, if present.",
        "- `MVP_HANDOFF.md`: short handoff note for Lou/Bowen.",
        "",
        "Current backend summary:",
    ]
    for row in summaries:
        lines.append(
            f"- {row.get('backend')}: status={row.get('run_status')}, "
            f"iterations={row.get('iteration_count')}, best_iter={row.get('best_iteration')}, "
            f"best_E={row.get('best_energy_eV')} eV"
        )
    lines.extend(
        [
            "",
            "Next when DFT structure arrives:",
            "1. Put the DFT optimized final structure path into `dft_reference_template.csv`.",
            "2. Compute site match, H position/height, bonded atoms, and geometric distance from each iteration to the DFT final state.",
            "3. Build Panel E from iteration snapshots + MACE trajectory, and Panel D from the DFT reference result.",
            "",
            "To refresh quick PNG snapshots after new XYZ files are added:",
            "`python3 research/agent_eval/render_dft_alignment_snapshots.py --case-dir <this directory>`",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_run(value: str) -> Tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--run must be BACKEND=RESULT_FULL_DIR")
    name, path = value.split("=", 1)
    return name.strip(), path.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="01")
    parser.add_argument("--output", default="research/results/analysis/dft_iteration_alignment/case_01")
    parser.add_argument(
        "--run",
        action="append",
        type=parse_run,
        help="Additional or replacement run in the form BACKEND=research/results/.../full",
    )
    parser.add_argument("--use-default-runs", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--overwrite-dft-template",
        action="store_true",
        help="Regenerate dft_reference_template.csv even if it already exists.",
    )
    args = parser.parse_args()

    output_dir = resolve_path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    runs: List[Tuple[str, str]] = []
    if args.use_default_runs:
        runs.extend(DEFAULT_RUNS)
    if args.run:
        runs.extend(args.run)

    all_rows: List[Dict[str, Any]] = []
    summaries: List[Dict[str, Any]] = []
    for backend, run_dir in runs:
        rows, summary = collect_run(args.case_id, backend, run_dir, output_dir)
        all_rows.extend(rows)
        summaries.append(summary)

    write_csv(output_dir / "agent_iteration_trajectory.csv", all_rows, TRAJECTORY_FIELDS)
    write_csv(output_dir / "agent_run_summary.csv", summaries, SUMMARY_FIELDS)
    write_csv(output_dir / "energy_curve.csv", energy_rows_from_trajectory(all_rows), ENERGY_FIELDS)
    write_energy_curve_svg(output_dir, all_rows)
    write_dft_template(output_dir, args.case_id, overwrite=args.overwrite_dft_template)
    write_readme(output_dir, args.case_id, summaries)
    write_handoff(output_dir, summaries, all_rows)
    write_file_manifest(output_dir)
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
