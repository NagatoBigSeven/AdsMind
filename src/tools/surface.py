"""Surface preparation and surface-site analysis helpers."""

from __future__ import annotations

from collections import Counter, defaultdict

import ase
import numpy as np
from ase.io import read
from autoadsorbate import Surface

from src.tools.constants import (
    MIN_CELL_SIZE_ANGSTROM,
    MIN_VACUUM_THICKNESS_ANGSTROM,
)
from src.tools.patches import apply_autoadsorbate_patches
from src.utils.logger import get_logger

logger = get_logger(__name__)

apply_autoadsorbate_patches()


def read_atoms_object(slab_path: str) -> ase.Atoms:
    """Read a structure file using ASE auto-detection."""
    try:
        atoms = read(slab_path)
        logger.info("Read slab atoms from %s.", slab_path)
        return atoms
    except Exception as exc:
        logger.error("Unable to read %s: %s", slab_path, exc)
        raise


def prepare_slab(slab_atoms: ase.Atoms) -> tuple[ase.Atoms, bool]:
    """
    Clean slab metadata and expand the supercell if needed.

    Returns a tuple of `(clean_slab, is_expanded)`.
    """
    logger.info("Preparing slab: cleaning metadata and validating dimensions")

    pbc = slab_atoms.get_pbc()
    if not any(pbc):
        logger.warning(
            "Input structure has no periodic boundary conditions (PBC). "
            "This typically indicates a molecular cluster (e.g., from PDB/MOL files), "
            "not a surface slab. AdsMind is designed for periodic surfaces; results may "
            "be unreliable."
        )
        logger.warning("Applying fallback XY periodic boundary conditions")
        slab_atoms.set_pbc([True, True, False])

        if slab_atoms.cell.volume < 1e-6:
            positions = slab_atoms.get_positions()
            min_pos = positions.min(axis=0)
            max_pos = positions.max(axis=0)
            extent = max_pos - min_pos

            cell_a = extent[0] + 15.0
            cell_b = extent[1] + 15.0
            cell_c = extent[2] + 20.0

            slab_atoms.set_cell([cell_a, cell_b, cell_c])
            slab_atoms.center()
            logger.info(
                "Created fallback cell: %.1f x %.1f x %.1f Å",
                cell_a,
                cell_b,
                cell_c,
            )

    symbols = slab_atoms.get_chemical_symbols()
    positions = slab_atoms.get_positions()
    cell = slab_atoms.get_cell()
    pbc = slab_atoms.get_pbc()

    clean_slab = ase.Atoms(symbols=symbols, positions=positions, cell=cell, pbc=pbc)

    cell_vectors = clean_slab.get_cell()
    a_len = np.linalg.norm(cell_vectors[0])
    b_len = np.linalg.norm(cell_vectors[1])

    mult_a = 2 if a_len < MIN_CELL_SIZE_ANGSTROM else 1
    mult_b = 2 if b_len < MIN_CELL_SIZE_ANGSTROM else 1
    is_expanded = mult_a > 1 or mult_b > 1
    if is_expanded:
        logger.info("Small cell detected. Expanding slab to %sx%sx1", mult_a, mult_b)
        clean_slab = clean_slab * (mult_a, mult_b, 1)

    cell_c = np.linalg.norm(clean_slab.get_cell()[2])
    z_coords = clean_slab.positions[:, 2]
    slab_thickness = z_coords.max() - z_coords.min()
    vacuum_thickness = cell_c - slab_thickness

    if vacuum_thickness < MIN_VACUUM_THICKNESS_ANGSTROM:
        logger.warning(
            "Vacuum layer thickness (%.1f Å) is less than recommended %.1f Å. "
            "This may cause spurious interactions between periodic images in Z.",
            vacuum_thickness,
            MIN_VACUUM_THICKNESS_ANGSTROM,
        )
    else:
        logger.info("Vacuum layer thickness: %.1f Å (OK)", vacuum_thickness)

    return clean_slab, is_expanded


def analyze_surface_sites(slab_path: str) -> dict:
    """Pre-scan the surface and describe available adsorption sites."""
    atoms = read_atoms_object(slab_path)
    clean_slab, _ = prepare_slab(atoms)

    logger.info("Starting surface site analysis")
    surface = Surface(clean_slab, precision=1.0, touch_sphere_size=2.0, mode="slab")
    logger.info("Surface site analysis found %s sites", len(surface.site_df))

    site_inventory = defaultdict(set)
    for _, row in surface.site_df.iterrows():
        conn = row["connectivity"]
        elements = []
        for element, count in row["site_formula"].items():
            elements.extend([element] * count)
        site_desc = "-".join(sorted(elements))
        site_inventory[conn].add(site_desc)

    desc_list = []
    conn_map = {1: "Ontop", 2: "Bridge", 3: "Hollow-3", 4: "Hollow-4"}
    for conn, sites in site_inventory.items():
        label = conn_map.get(conn, f"{conn}-fold")
        desc_list.append(f"[{label}]: {', '.join(sorted(list(sites)))}")

    return {
        "surface_composition": [
            item[0]
            for item in Counter(clean_slab.get_chemical_symbols()).most_common()
        ],
        "available_sites_description": "; ".join(desc_list),
    }
