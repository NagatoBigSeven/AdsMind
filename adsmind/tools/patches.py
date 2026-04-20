"""Autoadsorbate monkey patches used by the runtime."""

from __future__ import annotations

import itertools

import autoadsorbate.Surf
import autoadsorbate.autoadsorbate
import numpy as np
from ase import Atom, Atoms
from scipy.spatial.distance import cdist

from adsmind.tools.constants import (
    DEFAULT_PRECISION,
    EPSILON_TOLERANCE,
    Z_AXIS_PENETRATION_LIMIT,
)
from adsmind.utils.logger import get_logger

logger = get_logger(__name__)

_PATCHES_APPLIED = False


def get_shrinkwrap_grid_fixed(
    slab,
    precision,
    drop_increment=0.1,
    touch_sphere_size=2,
    marker="He",
    raster_speed_boost=False,
):
    """
    Fixed version of autoadsorbate's get_shrinkwrap_grid function.

    Prevents an infinite loop by stopping grid points from penetrating below the
    configured Z-axis lower bound.
    """
    from autoadsorbate.Surf import _get_starting_grid, get_large_atoms

    if raster_speed_boost:
        from autoadsorbate.raster_utilities import get_surface_from_rasterized_top_view

        raster_surf_index = get_surface_from_rasterized_top_view(
            slab, pixel_per_angstrom=10
        )
        slab = slab[raster_surf_index]

    starting_grid, faces = _get_starting_grid(slab, precision=precision)
    grid_positions = starting_grid.positions
    large_slab = get_large_atoms(slab)
    slab_positions = large_slab.positions

    distances_to_grid = cdist(grid_positions, slab_positions).min(axis=1)
    drop_vectors = np.array([[0, 0, drop_increment] for _ in grid_positions])

    while (
        (distances_to_grid > touch_sphere_size)
        & (grid_positions[:, 2] > Z_AXIS_PENETRATION_LIMIT)
    ).any():
        mask_to_move = (distances_to_grid > touch_sphere_size) & (
            grid_positions[:, 2] > Z_AXIS_PENETRATION_LIMIT
        )
        grid_positions -= drop_vectors * mask_to_move[:, np.newaxis]
        distances_to_grid = cdist(grid_positions, slab_positions).min(axis=1)

        if (distances_to_grid > touch_sphere_size).all() and (
            grid_positions[:, 2] <= 0
        ).all():
            break

    grid = Atoms(
        [marker for _ in grid_positions],
        grid_positions,
        pbc=[True, True, True],
        cell=slab.cell,
    )
    z_min = slab.positions[:, 2].min()
    grid = grid[[atom.index for atom in grid if atom.position[2] > z_min - 1.0]]
    grid.wrap()
    grid.arrays["wrapped_positions"] = grid.get_positions(wrap=True)

    return grid, faces


def get_shrinkwrap_ads_sites_fixed(
    atoms: Atoms,
    precision: float = DEFAULT_PRECISION,
    touch_sphere_size: float = 2,
    return_trj: bool = False,
    return_geometry=False,
):
    """Improved shrinkwrap site detection with more stable contact heuristics."""
    from autoadsorbate.Surf import (
        get_list_of_touching,
        get_shrinkwrap_grid,
        get_shrinkwrap_site_h_vector,
        get_shrinkwrap_site_n_vector,
        get_wrapped_site,
        shrinkwrap_surface,
    )

    grid, faces = get_shrinkwrap_grid(
        atoms, precision=precision, touch_sphere_size=touch_sphere_size
    )

    surf_ind = shrinkwrap_surface(
        atoms, precision=precision, touch_sphere_size=touch_sphere_size
    )

    targets = get_list_of_touching(
        atoms,
        grid,
        surf_ind,
        touch_sphere_size=touch_sphere_size,
        epsilon=EPSILON_TOLERANCE,
    )

    trj = []
    coordinates = []
    connectivity = []
    topology = []
    n_vector = []
    h_vector = []
    site_formula = []

    for target in targets:
        atoms_copy = atoms.copy()

        for index in target:
            atoms_copy.append(Atom("X", atoms_copy[index].position + [0, 0, 0]))

        extended_atoms = atoms_copy.copy() * [2, 2, 1]
        extended_grid = grid.copy() * [2, 2, 1]

        if len(target) == 1:
            site_atoms = atoms_copy[target]
            site_coord = site_atoms.positions[0]
        else:
            combs = []
            min_std_devs = []

            for combo in itertools.combinations(
                [atom.index for atom in extended_atoms if atom.symbol == "X"],
                len(target),
            ):
                combo = list(combo)
                min_std_devs.append(max(extended_atoms.positions[combo].std(axis=0)))
                combs.append(combo)

            min_std_devs = np.array(min_std_devs)
            min_comb_index = np.argmin(min_std_devs)

            site_atoms = extended_atoms[combs[min_comb_index]]
            site_coord = np.mean(site_atoms.positions, axis=0)
            site_coord = get_wrapped_site(site_coord, atoms_copy)
            site_coord = np.array(site_coord)

        n_vec = get_shrinkwrap_site_n_vector(
            extended_atoms, site_coord, extended_grid, touch_sphere_size
        )
        h_vec = get_shrinkwrap_site_h_vector(site_atoms, n_vec)
        site_form = atoms[target].symbols.formula.count()

        coordinates.append(site_coord)
        n_vector.append(n_vec)
        h_vector.append(h_vec)
        topology.append(target)
        connectivity.append(len(target))
        site_formula.append(site_form)

    sites_dict = {
        "coordinates": coordinates,
        "connectivity": connectivity,
        "topology": topology,
        "n_vector": n_vector,
        "h_vector": h_vector,
        "site_formula": site_formula,
    }

    if return_trj:
        extended_atoms = extended_atoms[
            [
                atom.index
                for atom in extended_atoms
                if np.linalg.norm(atom.position - site_coord) < 7
            ]
        ]
        for marker_index in range(20):
            extended_atoms.append(Atom("H", site_coord + n_vec * marker_index * 0.5))
        trj.append(extended_atoms)
        return sites_dict, trj

    if return_geometry:
        return grid.positions, faces, sites_dict

    return sites_dict


def apply_autoadsorbate_patches() -> None:
    """Apply the monkey patches once per interpreter session."""
    global _PATCHES_APPLIED

    if _PATCHES_APPLIED:
        return

    logger.info("Applying Autoadsorbate monkey patches for bug fixes")
    autoadsorbate.Surf.get_shrinkwrap_grid = get_shrinkwrap_grid_fixed
    autoadsorbate.Surf.get_shrinkwrap_ads_sites = get_shrinkwrap_ads_sites_fixed
    autoadsorbate.autoadsorbate.get_shrinkwrap_ads_sites = (
        get_shrinkwrap_ads_sites_fixed
    )
    _PATCHES_APPLIED = True
    logger.info("Autoadsorbate patches applied successfully")
