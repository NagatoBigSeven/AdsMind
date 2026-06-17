"""Fragment generation and surface population helpers."""

from __future__ import annotations

import json
import random
from collections import Counter
from typing import Union

import ase
import numpy as np
from ase import Atoms
from ase.io.trajectory import Trajectory
from autoadsorbate import Fragment, Surface
from rdkit import Chem
from rdkit.Chem import AllChem
from scipy.spatial.distance import cdist

from adsmind.tools.common import ensure_output_dir, sanitize_smiles_for_filename
from adsmind.tools.constants import (
    MIN_COLLISION_THRESHOLD_ANGSTROM,
    PRE_LIFT_HEIGHT_ANGSTROM,
)
from adsmind.tools.patches import apply_autoadsorbate_patches
from adsmind.utils.logger import get_logger

logger = get_logger(__name__)

apply_autoadsorbate_patches()


def get_atom_index_menu(original_smiles: str) -> str:
    """Return a JSON list describing heavy atoms in the input SMILES."""
    logger.info("Generating heavy atom index list for %s", original_smiles)
    try:
        mol = Chem.MolFromSmiles(original_smiles)
        if not mol:
            raise ValueError(f"RDKit cannot parse SMILES: {original_smiles}")

        atom_list = []
        for atom in mol.GetAtoms():
            atom_list.append(
                {
                    "index": atom.GetIdx(),
                    "symbol": atom.GetSymbol(),
                    "hybridization": str(atom.GetHybridization()),
                    "degree": atom.GetDegree(),
                    "radical_electrons": atom.GetNumRadicalElectrons(),
                    "formal_charge": atom.GetFormalCharge(),
                }
            )

        heavy_atom_menu = [atom for atom in atom_list if atom["symbol"] != "H"]
        logger.info("Generated heavy atom index list with %s entries", len(heavy_atom_menu))
        return json.dumps(heavy_atom_menu, indent=2)
    except Exception as exc:
        logger.error("get_atom_index_menu failed: %s", exc)
        return json.dumps({"error": f"Unable to generate heavy atom index list: {exc}"})


def generate_surrogate_smiles(
    original_smiles: str, binding_atom_indices: list[int], site_type: str
) -> str:
    """Generate a marker-augmented surrogate SMILES for AutoAdsorbate."""
    logger.info(
        "Calling SMILES translator: %s via indices %s (site=%s)",
        original_smiles,
        binding_atom_indices,
        site_type,
    )

    mol = Chem.MolFromSmiles(original_smiles)
    if not mol:
        raise ValueError(f"RDKit cannot parse original SMILES: {original_smiles}")

    num_binding_indices = len(binding_atom_indices)

    if site_type == "ontop":
        if num_binding_indices != 1:
            raise ValueError(
                f"'ontop' site requires 1 binding index, but got {num_binding_indices}."
            )

        target_idx = binding_atom_indices[0]
        if target_idx >= mol.GetNumAtoms():
            raise ValueError(
                f"Index {target_idx} out of range (atom count: {mol.GetNumAtoms()})."
            )

        target_atom_original = mol.GetAtomWithIdx(target_idx)
        original_h_count = target_atom_original.GetTotalNumHs()
        num_radicals = target_atom_original.GetNumRadicalElectrons()

        new_mol = Chem.RWMol(mol)

        marker_atom = Chem.Atom("Cl")
        marker_atom.SetAtomMapNum(1)
        marker_atom.SetIsotope(37)
        marker_idx = new_mol.AddAtom(marker_atom)

        if num_radicals > 0:
            logger.info(
                "Smart bonding selected covalent SINGLE bond because radical count=%s",
                num_radicals,
            )
            new_mol.AddBond(marker_idx, target_idx, Chem.rdchem.BondType.SINGLE)
            target_atom_obj = new_mol.GetAtomWithIdx(target_idx)
            target_atom_obj.SetNumRadicalElectrons(0)
        else:
            logger.info(
                "Smart bonding selected DATIVE bond for lone-pair style adsorption"
            )
            new_mol.AddBond(target_idx, marker_idx, Chem.rdchem.BondType.DATIVE)
            target_atom_obj = new_mol.GetAtomWithIdx(target_idx)

        target_atom_obj.SetNumExplicitHs(original_h_count)
        target_atom_obj.SetNoImplicit(True)
        target_atom_obj.SetAtomMapNum(114514)
        if target_atom_obj.GetSymbol() != "H":
            target_atom_obj.SetIsotope(14)

        try:
            Chem.SanitizeMol(new_mol)
        except Exception as exc:
            logger.warning("Sanitize warning while generating surrogate SMILES: %s", exc)

        out_smiles = Chem.MolToSmiles(
            new_mol.GetMol(), canonical=False, rootedAtAtom=marker_idx
        )
        logger.info("SMILES translator output: %s", out_smiles)
        return out_smiles

    if site_type in ["bridge", "hollow"]:
        if num_binding_indices == 1:
            target_idx = binding_atom_indices[0]
            if target_idx >= mol.GetNumAtoms():
                raise ValueError(f"Index {target_idx} out of range.")
            rw_mol = Chem.RWMol(mol)
            rw_mol.GetAtomWithIdx(target_idx).SetAtomMapNum(114514)
            original_smiles_mapped = Chem.MolToSmiles(rw_mol.GetMol(), canonical=False)
            out_smiles = f"{original_smiles_mapped}.[S:1].[S:2]"
            logger.info("SMILES translator output: %s", out_smiles)
            return out_smiles

        if num_binding_indices == 2:
            idx1, idx2 = sorted(binding_atom_indices)
            if idx2 >= mol.GetNumAtoms():
                raise ValueError(f"Index {idx2} out of range.")
            rw_mol = Chem.RWMol(mol)
            rw_mol.GetAtomWithIdx(idx1).SetAtomMapNum(114514)
            rw_mol.GetAtomWithIdx(idx2).SetAtomMapNum(1919810)
            original_smiles_mapped = Chem.MolToSmiles(rw_mol.GetMol(), canonical=False)
            out_smiles = f"{original_smiles_mapped}.[S:1].[S:2]"
            logger.info("SMILES translator output: %s", out_smiles)
            return out_smiles

        raise ValueError(
            f"'{site_type}' site does not support {num_binding_indices} binding indices."
        )

    raise ValueError(f"Unknown site_type: {site_type}.")


def _get_fragment(
    SMILES: str, site_type: str, num_binding_indices: int, to_initialize: int = 1
) -> Union[Fragment, ase.Atoms]:
    """Build a Fragment object with marker atoms ordered for AutoAdsorbate."""
    trick_smiles = "Cl" if site_type == "ontop" else "S1S"
    logger.info(
        "Preparing fragment markers for site=%s using marker=%s",
        site_type,
        trick_smiles,
    )

    try:
        mol = Chem.MolFromSmiles(SMILES, sanitize=False)
        if not mol:
            raise ValueError(f"RDKit cannot parse mapped SMILES: {SMILES}")
        mol.UpdatePropertyCache(strict=False)

        try:
            mol_with_hs = Chem.AddHs(mol)
        except Exception:
            mol_with_hs = mol

        mol_for_opt = Chem.Mol(mol_with_hs)
        has_charge = any(atom.GetFormalCharge() != 0 for atom in mol_for_opt.GetAtoms())

        for atom in mol_for_opt.GetAtoms():
            atom.SetFormalCharge(0)
            atom.SetNumRadicalElectrons(0)
            atom.SetIsotope(0)
            atom.SetHybridization(Chem.rdchem.HybridizationType.UNSPECIFIED)

        try:
            Chem.SanitizeMol(mol_for_opt)
        except Exception as exc:
            logger.warning("Sanitize warning while preparing fragment: %s", exc)

        params = AllChem.ETKDGv3()
        params.randomSeed = 0xF00D
        params.pruneRmsThresh = 0.5
        params.numThreads = 0

        conf_ids = list(
            AllChem.EmbedMultipleConfs(
                mol_for_opt, numConfs=to_initialize, params=params
            )
        )

        if not conf_ids:
            logger.warning("ETKDGv3 failed, trying ETKDGv2")
            AllChem.EmbedMolecule(mol_for_opt, AllChem.ETKDGv2())
            if mol_for_opt.GetNumConformers() > 0:
                conf_ids = [0]

        if not conf_ids:
            logger.warning("ETKDG series failed, trying random coordinates")
            params_rand = AllChem.ETKDGv3()
            params_rand.useRandomCoords = True
            conf_ids = list(
                AllChem.EmbedMultipleConfs(mol_for_opt, numConfs=1, params=params_rand)
            )

        if has_charge:
            logger.info("Charged atoms detected, skipping UFF pre-optimization")
        else:
            try:
                AllChem.UFFOptimizeMoleculeConfs(mol_for_opt)
            except Exception as exc:
                logger.warning("UFF optimization warning: %s", exc)

        mol_with_hs.RemoveAllConformers()
        for cid in conf_ids:
            conf_src = mol_for_opt.GetConformer(cid)
            mol_with_hs.AddConformer(Chem.Conformer(conf_src), assignId=True)

        reordered_conformers = []
        all_rdkit_atoms = list(mol_with_hs.GetAtoms())

        for conf_id in conf_ids:
            conf = mol_with_hs.GetConformer(conf_id)
            positions = conf.GetPositions()

            map_num_to_idx = {}
            for atom in all_rdkit_atoms:
                map_num = atom.GetAtomMapNum()
                idx = atom.GetIdx()
                iso = atom.GetIsotope()
                if map_num > 0:
                    map_num_to_idx[map_num] = idx
                if iso == 37:
                    map_num_to_idx[1] = idx
                if iso == 14:
                    map_num_to_idx[114514] = idx

            proxy_indices = []
            binding_indices = []

            if trick_smiles == "Cl":
                if num_binding_indices != 1:
                    raise ValueError(
                        "Logic error: TRICK_SMILES='Cl' but binding indices != 1"
                    )
                if 1 not in map_num_to_idx or 114514 not in map_num_to_idx:
                    raise ValueError(
                        f"SMILES {SMILES} missing map number 1 (Cl) or 114514."
                    )

                proxy_indices = [map_num_to_idx[1]]
                binding_indices = [map_num_to_idx[114514]]
                all_rdkit_atoms[map_num_to_idx[114514]].SetAtomMapNum(0)

            elif trick_smiles == "S1S":
                if 1 not in map_num_to_idx or 2 not in map_num_to_idx:
                    raise ValueError(
                        f"SMILES {SMILES} missing map number 1 (S1) or 2 (S2)."
                    )
                proxy_indices = [map_num_to_idx[1], map_num_to_idx[2]]

                if num_binding_indices == 1:
                    if 114514 not in map_num_to_idx:
                        raise ValueError(
                            f"SMILES {SMILES} missing map number 114514."
                        )

                    binding_indices = [map_num_to_idx[114514]]
                    s1_idx, s2_idx = proxy_indices[0], proxy_indices[1]
                    t1_idx = binding_indices[0]
                    p1 = positions[t1_idx]
                    v_perp = np.array([0.0, 0.5, 0.0])
                    midpoint = p1 - np.array([0.1, 0.0, 1.0])
                    positions[s1_idx] = midpoint + v_perp
                    positions[s2_idx] = midpoint - v_perp
                    logger.info(
                        "Aligned S-S marker for end-on mode using tilt correction"
                    )
                    all_rdkit_atoms[t1_idx].SetAtomMapNum(0)

                elif num_binding_indices == 2:
                    if 114514 not in map_num_to_idx or 1919810 not in map_num_to_idx:
                        raise ValueError(
                            f"SMILES {SMILES} missing map number 114514 or 1919810."
                        )

                    binding_indices = [map_num_to_idx[114514], map_num_to_idx[1919810]]
                    s1_idx, s2_idx = proxy_indices[0], proxy_indices[1]
                    t1_idx, t2_idx = binding_indices[0], binding_indices[1]

                    p1 = positions[t1_idx]
                    p2 = positions[t2_idx]
                    midpoint = (p1 + p2) / 2.0
                    v_bond = p1 - p2
                    norm = np.linalg.norm(v_bond)
                    v_bond_norm = np.array([1.0, 0.0, 0.0]) if norm < 1e-3 else v_bond / norm
                    positions[s1_idx] = midpoint + v_bond_norm * 0.5
                    positions[s2_idx] = midpoint - v_bond_norm * 0.5
                    logger.info(
                        "Aligned S-S vector parallel to bond axis for side-on mode"
                    )
                    all_rdkit_atoms[t1_idx].SetAtomMapNum(0)
                    all_rdkit_atoms[t2_idx].SetAtomMapNum(0)

            special_indices_set = set(proxy_indices + binding_indices)
            other_indices = [
                atom.GetIdx()
                for atom in all_rdkit_atoms
                if atom.GetIdx() not in special_indices_set and atom.GetAtomMapNum() == 0
            ]

            new_order = proxy_indices + binding_indices + other_indices
            new_symbols = [all_rdkit_atoms[i].GetSymbol() for i in new_order]
            new_positions = [positions[i] for i in new_order]

            new_atoms = Atoms(symbols=new_symbols, positions=new_positions)
            new_atoms.info = {"smiles": trick_smiles}
            reordered_conformers.append(new_atoms)

        if not reordered_conformers:
            raise ValueError(
                "RDKit conformer generation succeeded, but atom mapping trace failed "
                f"(SMILES: {SMILES})"
            )

        logger.info("Constructing Fragment shell with %s conformers", len(reordered_conformers))
        fragment = Fragment.__new__(Fragment)
        fragment.conformers = reordered_conformers
        fragment.conformers_aligned = [False] * len(reordered_conformers)
        fragment.smile = trick_smiles
        fragment.to_initialize = to_initialize
        logger.info("Fragment creation succeeded for %s", SMILES)
        return fragment

    except Exception as exc:
        logger.error("Unable to create Fragment from SMILES %s: %s", SMILES, exc)
        raise


def create_fragment_from_plan(
    original_smiles: str,
    binding_atom_indices: list[int],
    plan_dict: dict,
    to_initialize: int = 1,
) -> Fragment:
    """Generate and tag a Fragment object from the validated plan."""
    logger.info("Executing create_fragment_from_plan")

    plan_solution = plan_dict.get("solution", {})
    adsorbate_type = plan_dict.get("adsorbate_type")
    site_type = plan_solution.get("site_type")
    num_binding_indices = len(binding_atom_indices)

    if not site_type or not adsorbate_type:
        raise ValueError("plan_dict missing 'site_type' or 'adsorbate_type'.")

    surrogate_smiles = generate_surrogate_smiles(
        original_smiles=original_smiles,
        binding_atom_indices=binding_atom_indices,
        site_type=site_type,
    )

    fragment = _get_fragment(
        SMILES=surrogate_smiles,
        site_type=site_type,
        num_binding_indices=num_binding_indices,
        to_initialize=to_initialize,
    )

    if not hasattr(fragment, "info"):
        logger.info("Fragment object missing .info dictionary; adding one")
        fragment.info = {}

    fragment.info["plan_site_type"] = site_type
    fragment.info["plan_original_smiles"] = original_smiles
    fragment.info["plan_binding_atom_indices"] = binding_atom_indices
    fragment.info["plan_adsorbate_type"] = adsorbate_type

    logger.info("create_fragment_from_plan succeeded")
    return fragment


def _bump_adsorbate_to_safe_distance(
    slab_atoms: ase.Atoms,
    full_atoms: ase.Atoms,
    min_dist_threshold: float = MIN_COLLISION_THRESHOLD_ANGSTROM,
) -> ase.Atoms:
    """Bump the adsorbate upward if it initially overlaps with the slab."""
    n_slab = len(slab_atoms)
    adsorbate_indices = list(range(n_slab, len(full_atoms)))
    if not adsorbate_indices:
        return full_atoms

    slab_pos = full_atoms.positions[:n_slab]
    ads_pos = full_atoms.positions[n_slab:]
    dists = cdist(ads_pos, slab_pos)
    min_d = np.min(dists)

    if min_d < min_dist_threshold:
        bump_height = (min_dist_threshold - min_d) + 0.2
        logger.warning(
            "Collision detected: min_dist=%.2f Å < %.2f Å, bumping adsorbate by %.2f Å",
            min_d,
            min_dist_threshold,
            bump_height,
        )
        full_atoms.positions[adsorbate_indices, 2] += bump_height

    return full_atoms


def populate_surface_with_fragment(
    slab_atoms: ase.Atoms,
    fragment_object: Fragment,
    plan_solution: dict,
    session_id: str,
    **kwargs,
) -> str:
    """Populate a slab with fragment placements and persist the initial conformers."""
    if not hasattr(fragment_object, "info") or "plan_site_type" not in fragment_object.info:
        raise ValueError("Fragment object missing 'plan_site_type' info.")

    raw_site_type = plan_solution.get("site_type", "all")
    site_type = "hollow" if raw_site_type.lower().startswith("hollow") else raw_site_type
    conformers_per_site_cap = plan_solution.get("conformers_per_site_cap", 4)
    overlap_thr = plan_solution.get("overlap_thr", 0.1)
    touch_sphere_size = plan_solution.get("touch_sphere_size", 2)

    logger.info("Initializing surface population (touch_sphere_size=%s)", touch_sphere_size)

    clean_slab_atoms = ase.Atoms(
        symbols=slab_atoms.get_chemical_symbols(),
        positions=slab_atoms.get_positions(),
        cell=slab_atoms.get_cell(),
        pbc=slab_atoms.get_pbc(),
    )

    surface = Surface(
        clean_slab_atoms,
        precision=1.0,
        touch_sphere_size=touch_sphere_size,
        mode="slab",
    )

    original_site_count = len(surface.site_df)
    logger.info("Surface population found %s raw sites", original_site_count)

    if surface.site_df.empty or len(surface.site_df) == 0:
        raise ValueError(
            "Autoadsorbate failed to find any adsorption sites on the surface (0 sites found). "
            f"This might be due to inappropriate touch_sphere_size ({touch_sphere_size})."
        )

    site_df_filtered = surface.site_df
    if site_type == "ontop":
        site_df_filtered = surface.site_df[surface.site_df.connectivity == 1]
    elif site_type == "bridge":
        site_df_filtered = surface.site_df[surface.site_df.connectivity == 2]
    elif site_type == "hollow":
        site_df_filtered = surface.site_df[surface.site_df.connectivity >= 3]
    elif site_type != "all":
        raise ValueError(f"Unknown site_type: '{site_type}'.")

    allowed_symbols = plan_solution.get("surface_binding_atoms")
    if allowed_symbols and len(allowed_symbols) > 0:
        logger.info(
            "Filtering candidate sites by strict surface symbols match: %s",
            sorted(allowed_symbols),
        )
        target_counts = Counter(allowed_symbols)

        def check_symbols(site_formula_dict):
            if not site_formula_dict or not isinstance(site_formula_dict, dict):
                return False

            site_atoms_list = []
            for sym, count in site_formula_dict.items():
                site_atoms_list.extend([sym] * count)
            return Counter(site_atoms_list) == target_counts

        initial_count = len(site_df_filtered)
        site_df_filtered = site_df_filtered[
            site_df_filtered["site_formula"].apply(check_symbols)
        ]
        logger.info(
            "Surface symbol filter reduced candidate sites from %s to %s",
            initial_count,
            len(site_df_filtered),
        )

    surface.site_df = site_df_filtered
    site_index_arg = list(surface.site_df.index)

    max_sites_per_type = 8
    if len(site_index_arg) > max_sites_per_type:
        logger.info(
            "Sampling %s of %s sites for efficiency",
            max_sites_per_type,
            len(site_index_arg),
        )
        site_index_arg = random.sample(site_index_arg, max_sites_per_type)
        surface.site_df = surface.site_df.loc[site_index_arg]

    logger.info("Plan verified: searching %s '%s' sites", len(site_index_arg), site_type)

    if len(site_index_arg) == 0:
        raise ValueError(
            f"No sites of type '{site_type}' containing {allowed_symbols} found."
        )

    sample_rotation = True
    num_binding_indices = len(fragment_object.info["plan_binding_atom_indices"])
    if num_binding_indices == 2:
        logger.info("Two-index adsorption mode detected; disabling sample_rotation")
        sample_rotation = False

    logger.info(
        "Calling Surface.get_populated_sites with cap=%s overlap=%s",
        conformers_per_site_cap,
        overlap_thr,
    )
    raw_out_trj = surface.get_populated_sites(
        fragment=fragment_object,
        site_index=site_index_arg,
        sample_rotation=sample_rotation,
        mode="all",
        conformers_per_site_cap=conformers_per_site_cap,
        overlap_thr=overlap_thr,
        verbose=True,
    )

    if site_type in ["bridge", "hollow"]:
        logger.info(
            "Pre-lifting adsorbate by %.2f Å for %s placements",
            PRE_LIFT_HEIGHT_ANGSTROM,
            site_type,
        )
        for atoms in raw_out_trj:
            n_slab = len(slab_atoms)
            atoms.positions[n_slab:, 2] += PRE_LIFT_HEIGHT_ANGSTROM

    out_trj = []
    for atoms in raw_out_trj:
        safe_atoms = _bump_adsorbate_to_safe_distance(
            slab_atoms,
            atoms,
            min_dist_threshold=MIN_COLLISION_THRESHOLD_ANGSTROM,
        )
        out_trj.append(safe_atoms)

    logger.info("Generated %s initial configurations", len(out_trj))
    if not out_trj:
        raise ValueError(
            f"get_populated_sites failed to generate any configurations. "
            f"overlap_thr ({overlap_thr}) might be too strict."
        )

    output_dir = ensure_output_dir(session_id)
    clean_smiles = sanitize_smiles_for_filename(
        fragment_object.info["plan_original_smiles"]
    )
    traj_file = output_dir / f"conformers_{clean_smiles}.traj"
    traj = Trajectory(str(traj_file), "w")
    for atoms in out_trj:
        traj.write(atoms)
    traj.close()

    logger.info("Saved generated configurations to %s", traj_file)
    return str(traj_file)
