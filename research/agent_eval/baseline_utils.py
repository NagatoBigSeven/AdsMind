"""Utilities for non-LLM adsorption baselines."""

from __future__ import annotations

import csv
import json
import math
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
from ase import Atoms
from ase.constraints import FixAtoms
from ase.io import write
from ase.optimize import BFGS
from rdkit import Chem
from rdkit.Chem import AllChem

from adsmind.tools.constants import FIXED_BOTTOM_FRACTION


@dataclass
class CandidateRecord:
    """One relaxed baseline candidate."""

    label: str
    status: str
    adsorption_energy_eV: Optional[float] = None
    total_energy_eV: Optional[float] = None
    error: str = ""
    atoms: Optional[Atoms] = None
    metadata: Optional[Dict[str, Any]] = None
    structure_file: str = ""


def normalise_case_ids(cases: str | Iterable[str]) -> List[str]:
    """Normalize comma-separated or iterable case IDs to two-digit strings."""
    if isinstance(cases, str):
        raw_cases = [item.strip() for item in cases.split(",") if item.strip()]
    else:
        raw_cases = [str(item).strip() for item in cases if str(item).strip()]
    return [case.zfill(2) for case in raw_cases]


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    """Write a CSV file with a stable field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON with deterministic formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def init_mace_calculator(
    *,
    model: str = "small",
    device: str = "cpu",
    dtype: str = "float32",
    dispersion: bool = False,
):
    """Initialize a MACE-MP calculator across installed MACE variants."""
    import torch
    from mace.calculators import mace_mp

    compiler = getattr(torch, "compiler", None)
    if compiler is not None and not hasattr(compiler, "is_compiling"):
        compiler.is_compiling = lambda: False

    kwargs = {"model": model, "device": device, "default_dtype": dtype}
    try:
        return mace_mp(**kwargs, dispersion=dispersion)
    except TypeError:
        return mace_mp(**kwargs)


def build_adsorbate_from_smiles(smiles: str, seed: int = 42) -> Atoms:
    """Create an ASE adsorbate from SMILES using RDKit coordinates."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit cannot parse SMILES: {smiles}")
    mol = Chem.AddHs(mol)

    if mol.GetNumAtoms() == 1:
        atom = mol.GetAtomWithIdx(0)
        return Atoms(symbols=[atom.GetSymbol()], positions=[[0.0, 0.0, 0.0]])

    params = AllChem.ETKDGv3()
    params.randomSeed = int(seed)
    params.pruneRmsThresh = 0.5
    params.numThreads = 0

    embedded = AllChem.EmbedMolecule(mol, params)
    if embedded != 0:
        params.useRandomCoords = True
        embedded = AllChem.EmbedMolecule(mol, params)
    if embedded != 0:
        raise ValueError(f"RDKit conformer embedding failed for {smiles}")

    try:
        AllChem.UFFOptimizeMolecule(mol)
    except Exception:
        pass

    conformer = mol.GetConformer()
    symbols = [atom.GetSymbol() for atom in mol.GetAtoms()]
    positions = np.asarray(conformer.GetPositions(), dtype=float)
    atoms = Atoms(symbols=symbols, positions=positions)
    atoms.center(vacuum=8.0)
    return atoms


def choose_binding_indices(smiles: str, site_type: str) -> List[int]:
    """Select a deterministic default binding mode for heuristic placements."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit cannot parse SMILES: {smiles}")

    atoms = list(mol.GetAtoms())
    radical_indices = [
        atom.GetIdx()
        for atom in atoms
        if atom.GetNumRadicalElectrons() > 0 and atom.GetSymbol() != "H"
    ]
    if not radical_indices and mol.GetNumAtoms() == 1:
        return [0]
    if radical_indices:
        return [radical_indices[0]]

    oxygen_indices = [atom.GetIdx() for atom in atoms if atom.GetSymbol() == "O"]
    nitrogen_indices = [atom.GetIdx() for atom in atoms if atom.GetSymbol() == "N"]
    carbon_indices = [atom.GetIdx() for atom in atoms if atom.GetSymbol() == "C"]

    if site_type in {"bridge", "hollow"} and oxygen_indices:
        for oxygen_idx in oxygen_indices:
            oxygen = mol.GetAtomWithIdx(oxygen_idx)
            for neighbor in oxygen.GetNeighbors():
                bond = mol.GetBondBetweenAtoms(oxygen_idx, neighbor.GetIdx())
                if neighbor.GetSymbol() == "C" and bond.GetBondTypeAsDouble() >= 1.5:
                    return sorted([neighbor.GetIdx(), oxygen_idx])

    if oxygen_indices:
        return [oxygen_indices[0]]
    if nitrogen_indices:
        return [nitrogen_indices[0]]
    if carbon_indices:
        return [carbon_indices[0]]
    return [0]


def adsorbate_type_for_smiles(smiles: str) -> str:
    """Infer the AdsMind plan adsorbate_type field for a simple heuristic plan."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit cannot parse SMILES: {smiles}")
    if any(atom.GetNumRadicalElectrons() > 0 for atom in mol.GetAtoms()):
        return "ReactiveSpecies"
    return "Molecule"


def bottom_fixed_indices(slab: Atoms) -> List[int]:
    """Return bottom-third slab atom indices for standard relaxation."""
    z_coords = slab.positions[:, 2]
    threshold = z_coords.min() + (z_coords.max() - z_coords.min()) * FIXED_BOTTOM_FRACTION
    return [idx for idx, z_value in enumerate(z_coords) if z_value < threshold]


def surface_reference_energy(slab: Atoms, calc) -> float:
    """Single-point reference energy for a fixed bare surface."""
    surface = slab.copy()
    surface.calc = calc
    surface.set_constraint(FixAtoms(indices=list(range(len(surface)))))
    return float(surface.get_potential_energy())


def adsorbate_reference_energy(adsorbate: Atoms, calc, *, fmax: float, steps: int) -> float:
    """Relax and score an isolated adsorbate reference."""
    ads = adsorbate.copy()
    ads.calc = calc
    ads.set_cell([20.0, 20.0, 20.0])
    ads.set_pbc([False, False, False])
    ads.center()
    if len(ads) > 1:
        BFGS(ads, trajectory=None, logfile=None).run(fmax=fmax, steps=steps)
    return float(ads.get_potential_energy())


def relax_candidate(
    *,
    label: str,
    system: Atoms,
    slab: Atoms,
    calc,
    e_surface: float,
    e_adsorbate: float,
    fmax: float,
    steps: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> CandidateRecord:
    """Relax one adslab candidate and return total and adsorption energies."""
    started = time.perf_counter()
    atoms = system.copy()
    try:
        atoms.calc = calc
        atoms.set_constraint(FixAtoms(indices=bottom_fixed_indices(slab)))
        max_force = np.max(np.linalg.norm(atoms.get_forces(), axis=1))
        if (not np.isfinite(max_force)) or max_force > 500.0:
            raise ValueError(f"initial max force is abnormal: {max_force:.3f} eV/A")
        BFGS(atoms, trajectory=None, logfile=None).run(fmax=fmax, steps=steps)
        total = float(atoms.get_potential_energy())
        adsorption = total - e_surface - e_adsorbate
        if (not np.isfinite(total)) or (not np.isfinite(adsorption)) or total < -2000.0 or adsorption < -2000.0:
            raise ValueError(
                f"final energy is abnormal: total={total:.6f} eV, "
                f"adsorption={adsorption:.6f} eV"
            )
        meta = dict(metadata or {})
        meta["wall_clock_sec"] = time.perf_counter() - started
        return CandidateRecord(
            label=label,
            status="success",
            adsorption_energy_eV=adsorption,
            total_energy_eV=total,
            atoms=atoms,
            metadata=meta,
        )
    except Exception as exc:
        return CandidateRecord(
            label=label,
            status="error",
            error=f"{type(exc).__name__}: {exc}",
            metadata={**(metadata or {}), "traceback": traceback.format_exc(limit=5)},
        )


def summarize_candidate_records(
    *,
    records: Sequence[CandidateRecord],
    output_dir: Path,
    structure_prefix: str,
    top_n: int = 3,
) -> Dict[str, Any]:
    """Persist top structures and return a JSON-serializable case summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    successes = [record for record in records if record.status == "success"]
    successes.sort(key=lambda item: math.inf if item.adsorption_energy_eV is None else item.adsorption_energy_eV)

    artifact_dir = output_dir / "artifacts"
    top_payload = []
    for rank, record in enumerate(successes[:top_n], start=1):
        if record.atoms is None:
            continue
        filename = (
            f"{structure_prefix}_top{rank}_{record.label}_"
            f"E{record.adsorption_energy_eV:.6f}.xyz"
        ).replace("/", "-")
        path = artifact_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        atoms = record.atoms.copy()
        atoms.info["adsorption_energy_eV"] = record.adsorption_energy_eV
        atoms.info["total_energy_eV"] = record.total_energy_eV
        write(str(path), atoms)
        record.structure_file = str(path)
        top_payload.append(
            {
                "rank": rank,
                "label": record.label,
                "adsorption_energy_eV": record.adsorption_energy_eV,
                "total_energy_eV": record.total_energy_eV,
                "structure_file": str(path),
            }
        )

    energies = [
        float(record.adsorption_energy_eV)
        for record in successes
        if record.adsorption_energy_eV is not None
    ]
    serializable_records = []
    for record in records:
        serializable_records.append(
            {
                "label": record.label,
                "status": record.status,
                "adsorption_energy_eV": record.adsorption_energy_eV,
                "total_energy_eV": record.total_energy_eV,
                "error": record.error,
                "metadata": record.metadata or {},
                "structure_file": record.structure_file,
            }
        )

    summary = {
        "status": "success" if successes else "failed",
        "attempted": len(records),
        "successful": len(successes),
        "failed": len(records) - len(successes),
        "best_energy_eV": min(energies) if energies else None,
        "mean_energy_eV": float(np.mean(energies)) if energies else None,
        "std_energy_eV": float(np.std(energies, ddof=0)) if energies else None,
        "best_structure_file": top_payload[0]["structure_file"] if top_payload else "",
        "top_structures": top_payload,
        "records": serializable_records,
    }
    write_json(output_dir / "result.json", summary)
    return summary
