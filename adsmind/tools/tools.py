"""Backward-compatible facade for the tools package."""

from adsmind.tools.analysis import analyze_relaxation_results
from adsmind.tools.constants import RelaxationMode
from adsmind.tools.fragment import (
    create_fragment_from_plan,
    generate_surrogate_smiles,
    get_atom_index_menu,
    populate_surface_with_fragment,
)
from adsmind.tools.patches import (
    apply_autoadsorbate_patches,
    get_shrinkwrap_ads_sites_fixed,
    get_shrinkwrap_grid_fixed,
)
from adsmind.tools.relaxation import relax_atoms, save_ase_atoms
from adsmind.tools.surface import analyze_surface_sites, prepare_slab, read_atoms_object

apply_autoadsorbate_patches()

__all__ = [
    "RelaxationMode",
    "analyze_relaxation_results",
    "analyze_surface_sites",
    "apply_autoadsorbate_patches",
    "create_fragment_from_plan",
    "generate_surrogate_smiles",
    "get_atom_index_menu",
    "get_shrinkwrap_ads_sites_fixed",
    "get_shrinkwrap_grid_fixed",
    "populate_surface_with_fragment",
    "prepare_slab",
    "read_atoms_object",
    "relax_atoms",
    "save_ase_atoms",
]
