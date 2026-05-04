"""Prepare VASP/QE handoff structures for DFT validation."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ase.io import read, write

from research.agent_eval.baseline_utils import normalise_case_ids
from research.agent_eval.common import load_manifest_map, resolve_repo_path


MANIFEST_FIELDS = [
    "case_id",
    "source",
    "rank",
    "mace_energy_eV",
    "input_dir",
    "source_structure",
    "status",
    "notes",
]


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def resolve_artifact_path(result_dir: Path, result: Dict[str, Any], raw_path: str) -> Optional[Path]:
    """Resolve AdsMind output paths copied into the result artifact directory."""
    if not raw_path:
        return None
    direct = resolve_repo_path(raw_path)
    if direct.exists():
        return direct
    basename = Path(raw_path).name
    artifacts = result.get("artifact_paths", {})
    for value in artifacts.values():
        candidate = resolve_repo_path(value)
        if candidate.name == basename and candidate.exists():
            return candidate
    fallback = result_dir / "artifacts" / basename
    if fallback.exists():
        return fallback
    return None


def collect_adsmind_structures(adsmind_dir: Path, case_id: str, top_k: int) -> List[Dict[str, Any]]:
    """Collect top-k AdsMind structures from attempt records."""
    result_dir = adsmind_dir / case_id
    result_path = result_dir / "result.json"
    if not result_path.exists():
        return []
    with result_path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    records = []
    for record in result.get("attempt_records", []):
        if record.get("status") != "success":
            continue
        path = resolve_artifact_path(result_dir, result, record.get("best_structure_file", ""))
        if path is None:
            continue
        records.append(
            {
                "energy": float(record["most_stable_energy_eV"]),
                "path": path,
                "notes": record.get("actual_site_type", ""),
            }
        )
    records.sort(key=lambda item: item["energy"])
    return records[:top_k]


def collect_baseline_structures(baseline_dir: Path, case_id: str, top_k: int) -> List[Dict[str, Any]]:
    """Collect top-k structures from a baseline result.json."""
    result_path = baseline_dir / case_id / "result.json"
    if not result_path.exists():
        return []
    with result_path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    records = []
    for item in result.get("top_structures", [])[:top_k]:
        path = resolve_repo_path(item.get("structure_file", ""))
        if path.exists():
            records.append(
                {
                    "energy": item.get("adsorption_energy_eV"),
                    "path": path,
                    "notes": item.get("label", ""),
                }
            )
    return records


def collect_adsorbagent_structures(adsorbagent_dir: Path, case_id: str, top_k: int) -> List[Dict[str, Any]]:
    """Collect top-k final Adsorb-Agent structures by stored trajectory energy."""
    case_dirs = sorted(path for path in adsorbagent_dir.glob(f"{case_id}_*") if path.is_dir())
    if not case_dirs:
        return []
    traj_dir = case_dirs[0] / "traj"
    records = []
    for traj_path in sorted(traj_dir.glob("*.traj")):
        try:
            traj = read(str(traj_path), index=":")
            final = traj[-1]
            energy = float(final.get_potential_energy())
        except Exception:
            continue
        records.append({"energy": energy, "path": traj_path, "notes": "final trajectory frame"})
    records.sort(key=lambda item: item["energy"])
    return records[:top_k]


def clean_energy_label(value: Any) -> str:
    if value is None:
        return "NA"
    return re.sub(r"[^0-9A-Za-z_.-]", "_", f"{float(value):.6f}")


def write_structure_package(
    *,
    source_record: Dict[str, Any],
    output_dir: Path,
    case_id: str,
    source: str,
    rank: int,
) -> Dict[str, Any]:
    """Write POSCAR and CIF for one selected structure."""
    energy_label = clean_energy_label(source_record.get("energy"))
    target_dir = output_dir / f"case_{case_id}" / f"{source}_rank{rank}_E{energy_label}"
    target_dir.mkdir(parents=True, exist_ok=True)
    atoms = read(str(source_record["path"]), index=-1)
    atoms.calc = None
    atoms.set_constraint()
    write(str(target_dir / "POSCAR"), atoms, format="vasp", vasp5=True, direct=True)
    write(str(target_dir / "structure.cif"), atoms)
    with (target_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "case_id": case_id,
                "source": source,
                "rank": rank,
                "mace_energy_eV": source_record.get("energy"),
                "source_structure": str(source_record["path"]),
                "notes": source_record.get("notes", ""),
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
    return {
        "case_id": case_id,
        "source": source,
        "rank": rank,
        "mace_energy_eV": source_record.get("energy"),
        "input_dir": str(target_dir),
        "source_structure": str(source_record["path"]),
        "status": "ready",
        "notes": source_record.get("notes", ""),
    }


def write_templates(output_dir: Path) -> None:
    """Write conservative VASP and QE templates for handoff."""
    (output_dir / "INCAR.template").write_text(
        "\n".join(
            [
                "SYSTEM = AdsMind DFT validation single point",
                "ENCUT = 520",
                "EDIFF = 1E-5",
                "ISMEAR = 1",
                "SIGMA = 0.10",
                "IBRION = -1",
                "NSW = 0",
                "ISPIN = 2",
                "LREAL = Auto",
                "LASPH = .TRUE.",
                "GGA = PE",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "KPOINTS.template").write_text(
        "\n".join(["Gamma mesh", "0", "Gamma", "3 3 1", "0 0 0", ""]),
        encoding="utf-8",
    )
    (output_dir / "qe.pwi.template").write_text(
        "\n".join(
            [
                "&control",
                "  calculation = 'scf',",
                "  pseudo_dir = './pseudo',",
                "/",
                "&system",
                "  ecutwfc = 60,",
                "  ecutrho = 480,",
                "  occupations = 'smearing',",
                "  smearing = 'mv',",
                "  degauss = 0.01,",
                "/",
                "&electrons",
                "  conv_thr = 1.0d-6,",
                "/",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--manifest", default="datasets/cmu20/cmu20_manifest.csv")
    parser.add_argument("--adsmind-dir", required=True)
    parser.add_argument("--adsorbagent-dir", required=True)
    parser.add_argument("--random-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args(argv)

    manifest = load_manifest_map(args.manifest)
    output_dir = resolve_repo_path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_templates(output_dir)

    adsmind_dir = resolve_repo_path(args.adsmind_dir)
    adsorbagent_dir = resolve_repo_path(args.adsorbagent_dir)
    random_dir = resolve_repo_path(args.random_dir)
    rows: List[Dict[str, Any]] = []

    for case_id in normalise_case_ids(args.cases):
        case_meta = manifest.get(case_id, {})
        source_map = {
            "adsmind_full": collect_adsmind_structures(adsmind_dir, case_id, args.top_k),
            "adsorbagent": collect_adsorbagent_structures(adsorbagent_dir, case_id, args.top_k),
            "random": collect_baseline_structures(random_dir, case_id, args.top_k),
        }
        case_readme = [f"# DFT validation case {case_id}", "", json.dumps(case_meta, indent=2)]
        for source, records in source_map.items():
            if not records:
                rows.append(
                    {
                        "case_id": case_id,
                        "source": source,
                        "rank": "",
                        "mace_energy_eV": "",
                        "input_dir": "",
                        "source_structure": "",
                        "status": "missing",
                        "notes": "no source structures found",
                    }
                )
                continue
            for rank, record in enumerate(records, start=1):
                row = write_structure_package(
                    source_record=record,
                    output_dir=output_dir,
                    case_id=case_id,
                    source=source,
                    rank=rank,
                )
                rows.append(row)
                case_readme.append(
                    f"- {source} rank {rank}: {row['mace_energy_eV']} eV -> {row['input_dir']}"
                )
        case_dir = output_dir / f"case_{case_id}"
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "README.md").write_text("\n".join(case_readme) + "\n", encoding="utf-8")

    write_csv(output_dir / "manifest.csv", rows, MANIFEST_FIELDS)
    print(output_dir / "manifest.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
