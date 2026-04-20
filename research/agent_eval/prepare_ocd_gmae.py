"""Prepare a filtered OCD-GMAE subset manifest for AdsMind experiments."""

from __future__ import annotations

import argparse
import csv
import json
import os
import pickle
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import lmdb
from ase import Atoms
from ase.data import chemical_symbols
from ase.io import write

from research.agent_eval.common import resolve_repo_path

DEFAULT_LMDB_PATH = Path(os.environ.get("OCD_GMAE_LMDB_PATH", "datasets/OCD-GMAE/data.lmdb"))
DEFAULT_MANIFEST_PATH = Path("research/agent_eval/manifests/ocd_gmae_manifest.csv")
DEFAULT_SLAB_DIR = Path("research/agent_eval/generated_slabs/ocd_gmae")
DEFAULT_SUMMARY_PATH = Path("research/agent_eval/manifests/ocd_gmae_manifest_selection.json")
DEFAULT_PRIORITY_SMILES = [
    "[H]",
    "[OH]",
    "[NH2]",
    "[N]=N",
    "[NH]",
    "N",
    "[N]=O",
    "NO",
    "O=N",
    "[CH]=O",
    "C(=O)C",
    "CO",
    "C(C)O",
    "C[O]",
    "[CH2][O]",
    "C([CH2])O",
    "[CH3]",
    "[CH2]C",
]
GENERIC_REQUEST_TEMPLATE = (
    "Find the lowest-energy adsorption configuration for the adsorbate with "
    "SMILES {smiles} on the provided surface."
)
GENERIC_NOTES_TEMPLATE = (
    "OCD-GMAE source key={source_key}; original_ads_smi={original_ads_smi}; "
    "surface_formula={surface_formula}; y_relaxed={y_relaxed:.6f} eV; "
    "site={site_indices}"
)
MANIFEST_COLUMNS = [
    "case_id",
    "slab_file",
    "smiles",
    "user_request",
    "surface_family",
    "adsorbate_name",
    "miller_index",
    "reaction_class",
    "ablation_candidate",
    "notes",
    "source_key",
    "original_ads_smi",
    "surface_formula",
    "surface_elements",
    "bare_slab_atoms",
    "adsorbate_atoms",
    "y_relaxed",
    "site_indices",
    "selection_bucket",
]
KNOWN_ADSORBATES = {
    "[H]": {
        "mapped_smiles": "[H]",
        "adsorbate_name": "H",
        "user_request": "Find the lowest-energy adsorption configuration for atomic hydrogen on the provided surface.",
        "reaction_class": "HER",
        "selection_bucket": "cmu_exact",
    },
    "[OH]": {
        "mapped_smiles": "[OH]",
        "adsorbate_name": "OH",
        "user_request": "Find the lowest-energy adsorption configuration for hydroxyl radical on the provided surface.",
        "reaction_class": "ORR",
        "selection_bucket": "cmu_exact",
    },
}
NON_METAL_ELEMENTS = {
    "H",
    "He",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Te",
    "I",
    "Xe",
    "At",
    "Rn",
    "Og",
}


@dataclass(frozen=True)
class OCDCandidate:
    """Normalized metadata for a single OCD-GMAE record."""

    source_key: str
    raw_smiles: str
    mapped_smiles: str
    adsorbate_name: str
    user_request: str
    reaction_class: str
    selection_bucket: str
    slab_atoms: Atoms
    bare_slab_atoms: int
    adsorbate_atoms: int
    surface_formula: str
    surface_elements: tuple[str, ...]
    surface_family: str
    y_relaxed: float
    site_indices: tuple[int, ...]


def ensure_runtime_dependencies() -> None:
    """Require torch-geometric before unpickling OCD-GMAE Data objects."""
    try:
        import torch_geometric.data  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised by real runtime only
        raise RuntimeError(
            "prepare_ocd_gmae.py requires torch-geometric to unpickle OCD-GMAE "
            "records. Install it first, e.g. `python -m pip install torch-geometric`."
        ) from exc


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a filtered OCD-GMAE manifest for AdsMind experiments."
    )
    parser.add_argument("--lmdb-path", default=str(DEFAULT_LMDB_PATH), help="Path to OCD-GMAE data.lmdb")
    parser.add_argument(
        "--manifest-path",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Output CSV manifest path",
    )
    parser.add_argument(
        "--slab-dir",
        default=str(DEFAULT_SLAB_DIR),
        help="Directory for generated slab extxyz files",
    )
    parser.add_argument(
        "--summary-path",
        default=str(DEFAULT_SUMMARY_PATH),
        help="Optional JSON summary path",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=24,
        help="Maximum number of selected cases to export",
    )
    parser.add_argument(
        "--per-smiles",
        type=int,
        default=3,
        help="Maximum representative slabs to take per adsorbate SMILES",
    )
    parser.add_argument(
        "--max-slab-atoms",
        type=int,
        default=200,
        help="Exclude bare slabs with more than this many atoms",
    )
    parser.add_argument(
        "--priority-smiles",
        default=",".join(DEFAULT_PRIORITY_SMILES),
        help="Comma-separated adsorbate priority order",
    )
    return parser.parse_args(argv)


def _tensor_to_python(value: Any) -> Any:
    """Convert tensors/arrays/scalars into plain Python containers."""
    if value is None:
        return None
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _ensure_sequence(value: Any) -> list[Any]:
    """Normalize iterable values to a list."""
    converted = _tensor_to_python(value)
    if converted is None:
        return []
    if isinstance(converted, list):
        return converted
    if isinstance(converted, tuple):
        return list(converted)
    return [converted]


def _ensure_cell_matrix(value: Any) -> list[list[float]]:
    """Normalize an ASE cell matrix from the LMDB payload."""
    cell = _ensure_sequence(value)
    if len(cell) == 1 and isinstance(cell[0], list):
        return [[float(component) for component in row] for row in cell[0]]
    return [[float(component) for component in row] for row in cell]


def _normalize_atomic_numbers(value: Any) -> list[int]:
    """Convert tensor-like atomic numbers to integer Z values."""
    return [int(round(number)) for number in _ensure_sequence(value)]


def _normalize_positions(value: Any) -> list[list[float]]:
    """Convert tensor-like atomic positions into nested float lists."""
    return [[float(component) for component in coords] for coords in _ensure_sequence(value)]


def _surface_formula(numbers: Sequence[int]) -> tuple[str, tuple[str, ...]]:
    """Return an alphabetized composition string and element tuple."""
    counts = Counter(chemical_symbols[number] for number in numbers)
    elements = tuple(sorted(counts))
    formula = "".join(
        f"{element}{counts[element] if counts[element] > 1 else ''}"
        for element in elements
    )
    return formula, elements


def _contains_metal(elements: Iterable[str]) -> bool:
    """Treat slabs as catalytic surfaces only if at least one element is metallic."""
    return any(element not in NON_METAL_ELEMENTS for element in elements)


def _surface_family(elements: Sequence[str]) -> str:
    """Coarse surface family tag for the manifest metadata."""
    metal_elements = [element for element in elements if element not in NON_METAL_ELEMENTS]
    if len(metal_elements) > 1:
        return "intermetallic"
    if len(metal_elements) == 1 and len(elements) == 1:
        return "monometallic"
    if len(metal_elements) == 1:
        return "compound"
    return "nonmetallic"


def _adsorbate_metadata(smiles: str) -> dict[str, str]:
    """Map the dataset adsorbate to AdsMind-compatible manifest metadata."""
    if smiles in KNOWN_ADSORBATES:
        return dict(KNOWN_ADSORBATES[smiles])
    selection_bucket = "small_n_species" if "N" in smiles and "C" not in smiles else "small_organic"
    return {
        "mapped_smiles": smiles,
        "adsorbate_name": smiles,
        "user_request": GENERIC_REQUEST_TEMPLATE.format(smiles=smiles),
        "reaction_class": "GENERALIZATION",
        "selection_bucket": selection_bucket,
    }


def build_bare_slab_atoms(record: Any) -> Atoms:
    """Convert an OCD-GMAE record into an ASE slab with tag=2 atoms removed."""
    numbers = _normalize_atomic_numbers(getattr(record, "atomic_numbers"))
    positions = _normalize_positions(getattr(record, "pos"))
    tags = [int(tag) for tag in _ensure_sequence(getattr(record, "tags", []))]
    keep_mask = [tag != 2 for tag in tags] if tags else [True] * len(numbers)

    filtered_numbers = [number for number, keep in zip(numbers, keep_mask) if keep]
    filtered_positions = [coords for coords, keep in zip(positions, keep_mask) if keep]
    filtered_tags = [tag for tag, keep in zip(tags, keep_mask) if keep] if tags else []

    atoms = Atoms(
        numbers=filtered_numbers,
        positions=filtered_positions,
        cell=_ensure_cell_matrix(getattr(record, "cell")),
        pbc=(True, True, False),
    )
    if filtered_tags:
        atoms.set_tags(filtered_tags)
    return atoms


def build_candidate(source_key: str, record: Any, max_slab_atoms: int) -> Optional[OCDCandidate]:
    """Normalize one LMDB row, or return None if it should be excluded."""
    raw_smiles = str(getattr(record, "ads_smi", "")).strip()
    if not raw_smiles:
        return None

    slab_atoms = build_bare_slab_atoms(record)
    if len(slab_atoms) > max_slab_atoms:
        return None

    surface_formula, surface_elements = _surface_formula(_normalize_atomic_numbers(slab_atoms.numbers))
    if not _contains_metal(surface_elements):
        return None

    metadata = _adsorbate_metadata(raw_smiles)
    gmae_tags = [int(tag) for tag in _ensure_sequence(getattr(record, "gmae_tags", []))]
    site_indices = tuple(int(index) for index in _ensure_sequence(getattr(record, "site", [])))
    return OCDCandidate(
        source_key=source_key,
        raw_smiles=raw_smiles,
        mapped_smiles=metadata["mapped_smiles"],
        adsorbate_name=metadata["adsorbate_name"],
        user_request=metadata["user_request"],
        reaction_class=metadata["reaction_class"],
        selection_bucket=metadata["selection_bucket"],
        slab_atoms=slab_atoms,
        bare_slab_atoms=len(slab_atoms),
        adsorbate_atoms=sum(1 for tag in gmae_tags if tag == 2),
        surface_formula=surface_formula,
        surface_elements=surface_elements,
        surface_family=_surface_family(surface_elements),
        y_relaxed=float(getattr(record, "y_relaxed")),
        site_indices=site_indices,
    )


def load_candidates(
    *,
    lmdb_path: Path,
    priority_smiles: Sequence[str],
    max_slab_atoms: int,
) -> list[OCDCandidate]:
    """Load all supported candidates from the OCD-GMAE LMDB."""
    ensure_runtime_dependencies()
    env = lmdb.open(
        str(lmdb_path),
        subdir=lmdb_path.is_dir(),
        readonly=True,
        lock=False,
        readahead=False,
        meminit=False,
    )
    wanted = set(priority_smiles)
    candidates: list[OCDCandidate] = []
    with env.begin() as txn:
        for key, value in txn.cursor():
            record = pickle.loads(value)
            raw_smiles = str(getattr(record, "ads_smi", "")).strip()
            if raw_smiles not in wanted:
                continue
            candidate = build_candidate(key.decode("utf-8"), record, max_slab_atoms)
            if candidate is not None:
                candidates.append(candidate)
    env.close()
    return candidates


def pick_group_representatives(
    candidates: Sequence[OCDCandidate],
    per_smiles: int,
) -> list[OCDCandidate]:
    """Pick low/mid/high-energy representatives with unique surface formulas."""
    if not candidates or per_smiles <= 0:
        return []
    ordered = sorted(
        candidates,
        key=lambda candidate: (
            candidate.y_relaxed,
            candidate.surface_formula,
            candidate.source_key,
        ),
    )
    positions = [0, len(ordered) // 2, len(ordered) - 1]
    picked: list[OCDCandidate] = []
    seen_keys: set[str] = set()
    seen_formulas: set[str] = set()

    for position in positions:
        candidate = ordered[position]
        if candidate.source_key in seen_keys or candidate.surface_formula in seen_formulas:
            continue
        picked.append(candidate)
        seen_keys.add(candidate.source_key)
        seen_formulas.add(candidate.surface_formula)
        if len(picked) >= per_smiles:
            return picked

    for candidate in ordered:
        if len(picked) >= per_smiles:
            break
        if candidate.source_key in seen_keys or candidate.surface_formula in seen_formulas:
            continue
        picked.append(candidate)
        seen_keys.add(candidate.source_key)
        seen_formulas.add(candidate.surface_formula)
    return picked


def select_candidates(
    candidates: Sequence[OCDCandidate],
    *,
    priority_smiles: Sequence[str],
    max_cases: int,
    per_smiles: int,
) -> list[OCDCandidate]:
    """Select a round-robin subset across the prioritized adsorbate list."""
    grouped: dict[str, list[OCDCandidate]] = {smiles: [] for smiles in priority_smiles}
    for candidate in candidates:
        grouped.setdefault(candidate.mapped_smiles, []).append(candidate)

    representative_map = {
        smiles: pick_group_representatives(grouped.get(smiles, []), per_smiles)
        for smiles in priority_smiles
    }
    selected: list[OCDCandidate] = []
    used_keys: set[str] = set()

    for round_index in range(per_smiles):
        for smiles in priority_smiles:
            representatives = representative_map.get(smiles, [])
            if round_index >= len(representatives):
                continue
            candidate = representatives[round_index]
            if candidate.source_key in used_keys:
                continue
            selected.append(candidate)
            used_keys.add(candidate.source_key)
            if len(selected) >= max_cases:
                return selected

    if len(selected) >= max_cases:
        return selected

    fallback = sorted(
        candidates,
        key=lambda candidate: (
            priority_smiles.index(candidate.mapped_smiles)
            if candidate.mapped_smiles in priority_smiles
            else len(priority_smiles),
            candidate.y_relaxed,
            candidate.source_key,
        ),
    )
    for candidate in fallback:
        if candidate.source_key in used_keys:
            continue
        selected.append(candidate)
        used_keys.add(candidate.source_key)
        if len(selected) >= max_cases:
            break
    return selected


def _sanitize_slug(text: str) -> str:
    """Create a filesystem-friendly token."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._")
    return slug or "item"


def write_outputs(
    *,
    selected: Sequence[OCDCandidate],
    manifest_path: Path,
    slab_dir: Path,
    repo_root: Path,
    summary_path: Optional[Path],
) -> dict[str, Any]:
    """Persist slab files, manifest CSV, and optional JSON summary."""
    slab_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(selected, start=1):
        case_id = f"{index:03d}"
        slab_name = (
            f"{case_id}_ocd_{_sanitize_slug(candidate.source_key)}_"
            f"{_sanitize_slug(candidate.surface_formula)}_"
            f"{_sanitize_slug(candidate.mapped_smiles)}.xyz"
        )
        slab_path = slab_dir / slab_name
        write(slab_path, candidate.slab_atoms, format="extxyz")
        try:
            slab_file_value = str(slab_path.relative_to(repo_root))
        except ValueError:
            slab_file_value = str(slab_path)

        notes = GENERIC_NOTES_TEMPLATE.format(
            source_key=candidate.source_key,
            original_ads_smi=candidate.raw_smiles,
            surface_formula=candidate.surface_formula,
            y_relaxed=candidate.y_relaxed,
            site_indices=list(candidate.site_indices),
        )
        row = {
            "case_id": case_id,
            "slab_file": slab_file_value,
            "smiles": candidate.mapped_smiles,
            "user_request": candidate.user_request,
            "surface_family": candidate.surface_family,
            "adsorbate_name": candidate.adsorbate_name,
            "miller_index": "",
            "reaction_class": candidate.reaction_class,
            "ablation_candidate": "FALSE",
            "notes": notes,
            "source_key": candidate.source_key,
            "original_ads_smi": candidate.raw_smiles,
            "surface_formula": candidate.surface_formula,
            "surface_elements": ";".join(candidate.surface_elements),
            "bare_slab_atoms": str(candidate.bare_slab_atoms),
            "adsorbate_atoms": str(candidate.adsorbate_atoms),
            "y_relaxed": f"{candidate.y_relaxed:.6f}",
            "site_indices": ";".join(str(index) for index in candidate.site_indices),
            "selection_bucket": candidate.selection_bucket,
        }
        manifest_rows.append(row)
        summary_rows.append(
            {
                "case_id": case_id,
                "slab_file": slab_file_value,
                "smiles": candidate.mapped_smiles,
                "source_key": candidate.source_key,
                "surface_formula": candidate.surface_formula,
                "bare_slab_atoms": candidate.bare_slab_atoms,
                "adsorbate_atoms": candidate.adsorbate_atoms,
                "y_relaxed": candidate.y_relaxed,
                "selection_bucket": candidate.selection_bucket,
            }
        )

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary_payload = {
        "manifest_path": str(manifest_path),
        "slab_dir": str(slab_dir),
        "selected_case_count": len(manifest_rows),
        "selected_counts_by_smiles": dict(Counter(row["smiles"] for row in manifest_rows)),
        "selected_cases": summary_rows,
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return summary_payload


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    lmdb_path = Path(args.lmdb_path).expanduser().resolve()
    manifest_path = resolve_repo_path(args.manifest_path, repo_root=repo_root)
    slab_dir = resolve_repo_path(args.slab_dir, repo_root=repo_root)
    summary_path = resolve_repo_path(args.summary_path, repo_root=repo_root) if args.summary_path else None
    priority_smiles = [value.strip() for value in args.priority_smiles.split(",") if value.strip()]

    try:
        candidates = load_candidates(
            lmdb_path=lmdb_path,
            priority_smiles=priority_smiles,
            max_slab_atoms=args.max_slab_atoms,
        )
    except RuntimeError as exc:
        print(str(exc))
        return 2

    selected = select_candidates(
        candidates,
        priority_smiles=priority_smiles,
        max_cases=args.max_cases,
        per_smiles=args.per_smiles,
    )
    summary = write_outputs(
        selected=selected,
        manifest_path=manifest_path,
        slab_dir=slab_dir,
        repo_root=repo_root,
        summary_path=summary_path,
    )
    print(
        json.dumps(
            {
                "lmdb_path": str(lmdb_path),
                "candidate_count": len(candidates),
                "selected_case_count": summary["selected_case_count"],
                "selected_counts_by_smiles": summary["selected_counts_by_smiles"],
                "manifest_path": str(manifest_path),
                "slab_dir": str(slab_dir),
                "summary_path": str(summary_path) if summary_path is not None else None,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
