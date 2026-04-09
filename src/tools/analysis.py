"""Post-relaxation structure analysis helpers."""

from __future__ import annotations

import json
import traceback

import ase
import numpy as np
from ase.io import read, write
from ase.neighborlist import build_neighbor_list, natural_cutoffs
from scipy.sparse.csgraph import connected_components

from src.tools.common import ensure_output_dir, sanitize_smiles_for_filename
from src.tools.constants import (
    BASE_BOND_MULTIPLIER,
    HCP_DETECTION_RADIUS_ANGSTROM,
    STRONG_ADSORPTION_BOND_MULTIPLIER,
    STRONG_ADSORPTION_THRESHOLD_EV,
    SUBSURFACE_LOWER_BOUND_ANGSTROM,
    SUBSURFACE_UPPER_BOUND_ANGSTROM,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_relaxation_results(
    relaxed_trajectory_file: str,
    slab_atoms: ase.Atoms,
    original_smiles: str,
    plan_dict: dict,
    session_id: str,
    e_surface_ref: float = 0.0,
    e_adsorbate_ref: float = 0.0,
) -> str:
    """Analyze relaxed structures and summarize the most stable adsorption state."""
    try:
        logger.info("Analyzing relaxation results from %s", relaxed_trajectory_file)

        try:
            traj = read(relaxed_trajectory_file, index=":")
        except Exception as read_error:
            return json.dumps(
                {
                    "status": "error",
                    "message": (
                        "Unable to read trajectory file (possibly corrupted): "
                        f"{read_error}"
                    ),
                }
            )

        if len(traj) == 0:
            return json.dumps(
                {"status": "error", "message": "Relaxation trajectory is empty or unreadable."}
            )

        energies = []
        for atoms in traj:
            try:
                energies.append(atoms.get_potential_energy())
            except Exception:
                pass

        min_energy_total = min(energies)
        best_index = np.argmin(energies)
        relaxed_atoms = traj[best_index]

        e_ads = min_energy_total - e_surface_ref - e_adsorbate_ref
        logger.info(
            "Analysis E_ads = %.4f eV (E_total=%.4f, E_surface=%.4f, E_adsorbate=%.4f)",
            e_ads,
            min_energy_total,
            e_surface_ref,
            e_adsorbate_ref,
        )

        def check_bonding_smart(atom_idx_1, atom_idx_2, r1, r2, current_energy_eV, check_atoms_obj):
            base_mult = BASE_BOND_MULTIPLIER
            if current_energy_eV < STRONG_ADSORPTION_THRESHOLD_EV:
                base_mult = STRONG_ADSORPTION_BOND_MULTIPLIER

            distance = check_atoms_obj.get_distance(atom_idx_1, atom_idx_2, mic=True)
            threshold = (r1 + r2) * base_mult
            return distance <= threshold, distance, threshold

        adsorbate_atoms = relaxed_atoms[len(slab_atoms):]
        check_atoms = adsorbate_atoms.copy()
        check_atoms.set_cell(relaxed_atoms.get_cell())
        check_atoms.set_pbc(relaxed_atoms.get_pbc())

        check_cutoffs = natural_cutoffs(check_atoms, mult=1.35)
        nl = build_neighbor_list(check_atoms, cutoffs=check_cutoffs, self_interaction=False)
        adjacency_matrix = nl.get_connectivity_matrix()

        n_components, labels = connected_components(adjacency_matrix, directed=False)
        is_dissociated = n_components > 1

        bond_change_count = relaxed_atoms.info.get("bond_change_count", 0)
        if is_dissociated and bond_change_count == 0:
            logger.warning(
                "Dissociation detected (n_components=%s) but bond_change_count=0; correcting to preserve consistency",
                n_components,
            )
            bond_change_count = max(1, n_components - 1)

        reaction_detected = is_dissociated or bond_change_count > 0

        plan_solution = plan_dict.get("solution", {})
        binding_atom_indices = plan_solution.get("adsorbate_binding_indices", [])
        num_binding_indices = len(binding_atom_indices)

        planned_info = relaxed_atoms.info.get("adsorbate_info", {}).get("site", {})
        planned_connectivity = planned_info.get("connectivity")
        planned_site_type = "unknown"
        if planned_connectivity == 1:
            planned_site_type = "ontop"
        elif planned_connectivity == 2:
            planned_site_type = "bridge"
        elif planned_connectivity and planned_connectivity >= 3:
            planned_site_type = "hollow"

        slab_indices_check = list(range(len(slab_atoms)))
        adsorbate_indices_check = list(range(len(slab_atoms), len(relaxed_atoms)))
        cov_cutoffs_check = natural_cutoffs(relaxed_atoms, mult=1)

        actual_bonded_slab_indices = set()
        anchor_atom_indices = []
        if num_binding_indices == 1 and len(adsorbate_indices_check) > 0:
            anchor_atom_indices = [adsorbate_indices_check[0]]
        elif num_binding_indices == 2 and len(adsorbate_indices_check) >= 2:
            anchor_atom_indices = [adsorbate_indices_check[0], adsorbate_indices_check[1]]

        for anchor_idx in anchor_atom_indices:
            r_ads = cov_cutoffs_check[anchor_idx]
            for slab_idx in slab_indices_check:
                r_slab = cov_cutoffs_check[slab_idx]
                is_connected, _, _ = check_bonding_smart(
                    anchor_idx,
                    slab_idx,
                    r_ads,
                    r_slab,
                    e_ads,
                    relaxed_atoms,
                )
                if is_connected:
                    actual_bonded_slab_indices.add(slab_idx)

        actual_connectivity = len(actual_bonded_slab_indices)
        actual_site_type = "unknown"
        if actual_connectivity == 1:
            actual_site_type = "ontop"
        elif actual_connectivity == 2:
            actual_site_type = "bridge"
        elif actual_connectivity >= 3:
            actual_site_type = "hollow"
        else:
            actual_site_type = "desorbed"

        if actual_site_type == "desorbed" and e_ads < STRONG_ADSORPTION_THRESHOLD_EV:
            logger.warning(
                "Strong adsorption energy %.2f eV with geometrically desorbed state; forcing inferred hollow label",
                e_ads,
            )
            actual_site_type = "hollow (inferred)"
            if actual_connectivity == 0:
                actual_connectivity = 3

        slab_indices = list(range(len(slab_atoms)))
        adsorbate_indices = list(range(len(slab_atoms), len(relaxed_atoms)))
        slab_atoms_relaxed = relaxed_atoms[slab_indices]

        target_atom_global_index = adsorbate_indices[0] if len(adsorbate_indices) > 0 else -1

        site_crystallography = ""
        if actual_site_type == "hollow":
            try:
                z_coords = slab_atoms_relaxed.positions[:, 2]
                max_z = np.max(z_coords)
                subsurface_mask = (z_coords < (max_z - SUBSURFACE_LOWER_BOUND_ANGSTROM)) & (
                    z_coords > (max_z - SUBSURFACE_UPPER_BOUND_ANGSTROM)
                )
                subsurface_indices_list = np.where(subsurface_mask)[0]

                if len(subsurface_indices_list) > 0:
                    target_pos_xy = relaxed_atoms[target_atom_global_index].position[:2]
                    subsurface_positions_xy = slab_atoms_relaxed.positions[
                        subsurface_indices_list
                    ][:, :2]
                    dists_xy = np.linalg.norm(subsurface_positions_xy - target_pos_xy, axis=1)
                    min_dist_xy = np.min(dists_xy)

                    if min_dist_xy < HCP_DETECTION_RADIUS_ANGSTROM:
                        site_crystallography = "(HCP/Subsurf-Atom)"
                    else:
                        site_crystallography = "(FCC/No-Subsurf)"
                else:
                    site_crystallography = "(Unknown Layer)"
            except Exception as cryst_error:
                logger.warning("Crystallographic analysis warning: %s", cryst_error)

        if site_crystallography:
            actual_site_type += f" {site_crystallography}"

        logger.info(
            "Site slip check: planned %s (conn=%s), actual %s (conn=%s)",
            planned_site_type,
            planned_connectivity,
            actual_site_type,
            actual_connectivity,
        )

        cov_cutoffs = natural_cutoffs(relaxed_atoms, mult=1)

        if num_binding_indices == 1:
            target_atom_global_index = adsorbate_indices[0]
            target_atom_symbol = relaxed_atoms[target_atom_global_index].symbol

            logger.info(
                "Single-index adsorption analysis on atom %s at global index %s",
                target_atom_symbol,
                target_atom_global_index,
            )

            bonded_surface_atoms = []
            min_distance = float("inf")
            nearest_slab_atom_symbol = ""
            nearest_slab_atom_global_index = -1
            bonding_cutoff = 0.0

            for slab_idx in slab_indices:
                r_ads = cov_cutoffs_check[target_atom_global_index]
                r_slab = cov_cutoffs_check[slab_idx]
                is_connected, distance, threshold = check_bonding_smart(
                    target_atom_global_index,
                    slab_idx,
                    r_ads,
                    r_slab,
                    e_ads,
                    relaxed_atoms,
                )

                if distance < min_distance:
                    min_distance = distance
                    nearest_slab_atom_global_index = slab_idx
                    nearest_slab_atom_symbol = relaxed_atoms[slab_idx].symbol
                    bonding_cutoff = threshold

                if is_connected:
                    bonded_surface_atoms.append(
                        {
                            "symbol": relaxed_atoms[slab_idx].symbol,
                            "index": slab_idx,
                            "distance": round(distance, 3),
                        }
                    )

            bonded_surface_atoms.sort(key=lambda item: item["distance"])
            site_fingerprint = "-".join(
                [f"{item['symbol']}{item['index']}" for item in bonded_surface_atoms]
            )

            is_bound = len(bonded_surface_atoms) > 0
            bonded_desc = (
                ", ".join(
                    [f"{item['symbol']}-{item['distance']}Å" for item in bonded_surface_atoms]
                )
                if is_bound
                else "None"
            )

            nearest_radius_sum = (
                cov_cutoffs[target_atom_global_index]
                + cov_cutoffs[nearest_slab_atom_global_index]
            )
            estimated_covalent_cutoff_a = nearest_radius_sum * 1.1

            planned_symbols = sorted(plan_solution.get("surface_binding_atoms", []))
            actual_symbols = sorted([atom["symbol"] for atom in bonded_surface_atoms])

            is_chemical_slip = False
            if planned_symbols and bonded_surface_atoms and planned_symbols != actual_symbols:
                is_chemical_slip = True
                logger.warning(
                    "Chemical site slip detected: planned=%s actual=%s",
                    planned_symbols,
                    actual_symbols,
                )

            analysis_message = (
                f"Most stable config adsorption energy: {e_ads:.4f} eV. "
                f"Target Atom: {target_atom_symbol} (from plan index {binding_atom_indices[0]}, "
                f"global index {target_atom_global_index} in relaxed structure). "
                f"-> Nearest: {nearest_slab_atom_symbol} (Index {nearest_slab_atom_global_index}), "
                f"Distance: {round(min_distance, 3)} Å (Threshold: {round(bonding_cutoff, 3)}), "
                f"Bound: {is_bound}. Bonded Surface Atoms: {bonded_desc}. "
                f"Is Bound: {is_bound}. Reactivity Change Detected: {reaction_detected} "
                f"(Bond Changes: {bond_change_count}). Chemical Slip: {is_chemical_slip} "
                f"(Planned {planned_symbols} -> Actual {actual_symbols})."
            )

            result = {
                "status": "success",
                "message": analysis_message,
                "most_stable_energy_eV": e_ads,
                "target_adsorbate_atom": target_atom_symbol,
                "target_adsorbate_atom_index": int(target_atom_global_index),
                "bonded_surface_atoms": bonded_surface_atoms,
                "nearest_slab_atom": nearest_slab_atom_symbol,
                "nearest_slab_atom_index": int(nearest_slab_atom_global_index),
                "final_bond_distance_A": round(min_distance, 3),
                "estimated_covalent_cutoff_A": round(estimated_covalent_cutoff_a, 3),
                "is_covalently_bound": bool(is_bound),
                "reaction_detected": bool(reaction_detected),
                "is_dissociated": bool(is_dissociated),
                "n_components": int(n_components),
                "bond_change_count": int(bond_change_count),
                "site_analysis": {
                    "planned_site_type": planned_site_type,
                    "planned_connectivity": planned_connectivity,
                    "actual_site_type": actual_site_type,
                    "actual_connectivity": actual_connectivity,
                    "is_chemical_slip": is_chemical_slip,
                    "planned_symbols": planned_symbols,
                    "actual_symbols": actual_symbols,
                    "site_fingerprint": site_fingerprint,
                },
            }

        elif num_binding_indices == 2:
            if len(adsorbate_indices) < 2:
                return json.dumps(
                    {
                        "status": "error",
                        "message": (
                            "Side-on mode requires at least 2 adsorbate atoms, "
                            f"but found {len(adsorbate_indices)}."
                        ),
                    }
                )

            target_atom_global_index = adsorbate_indices[0]
            target_atom_symbol = relaxed_atoms[target_atom_global_index].symbol
            target_atom_pos = relaxed_atoms[target_atom_global_index].position
            logger.info(
                "Two-index adsorption analysis on first atom %s at global index %s",
                target_atom_symbol,
                target_atom_global_index,
            )

            distances = np.linalg.norm(slab_atoms.positions - target_atom_pos, axis=1)
            min_distance = np.min(distances)
            nearest_slab_atom_global_index = slab_indices[np.argmin(distances)]
            nearest_slab_atom_symbol = relaxed_atoms[nearest_slab_atom_global_index].symbol
            radius_1 = cov_cutoffs[target_atom_global_index]
            radius_2 = cov_cutoffs[nearest_slab_atom_global_index]
            bonding_cutoff = (radius_1 + radius_2) * 1.1
            is_bound_1 = min_distance <= bonding_cutoff

            second_atom_global_index = adsorbate_indices[1]
            second_atom_symbol = relaxed_atoms[second_atom_global_index].symbol
            second_atom_pos = relaxed_atoms[second_atom_global_index].position
            logger.info(
                "Two-index adsorption analysis on second atom %s at global index %s",
                second_atom_symbol,
                second_atom_global_index,
            )

            distances_2 = np.linalg.norm(slab_atoms.positions - second_atom_pos, axis=1)
            min_distance_2 = np.min(distances_2)
            nearest_slab_atom_global_index_2 = slab_indices[np.argmin(distances_2)]
            nearest_slab_atom_symbol_2 = relaxed_atoms[nearest_slab_atom_global_index_2].symbol
            radius_3 = cov_cutoffs[second_atom_global_index]
            radius_4 = cov_cutoffs[nearest_slab_atom_global_index_2]
            bonding_cutoff_2 = (radius_3 + radius_4) * 1.1
            is_bound_2 = min_distance_2 <= bonding_cutoff_2

            is_bound = bool(is_bound_1 and is_bound_2)
            bonded_surface_atoms = []

            def find_bonds(ads_idx, ads_symbol):
                bonds = []
                r_ads = cov_cutoffs_check[ads_idx]
                for slab_idx in slab_indices:
                    r_slab = cov_cutoffs_check[slab_idx]
                    is_connected, distance, _ = check_bonding_smart(
                        ads_idx,
                        slab_idx,
                        r_ads,
                        r_slab,
                        e_ads,
                        relaxed_atoms,
                    )
                    if is_connected:
                        bonds.append(
                            {
                                "adsorbate_atom": f"{ads_symbol}({ads_idx})",
                                "adsorbate_atom_index": int(ads_idx),
                                "symbol": relaxed_atoms[slab_idx].symbol,
                                "index": int(slab_idx),
                                "distance": round(distance, 3),
                            }
                        )
                return bonds

            bonded_surface_atoms.extend(find_bonds(target_atom_global_index, target_atom_symbol))
            bonded_surface_atoms.extend(find_bonds(second_atom_global_index, second_atom_symbol))
            bonded_surface_atoms.sort(key=lambda item: item["distance"])
            site_fingerprint = "-".join(
                [f"{item['symbol']}{item['index']}" for item in bonded_surface_atoms]
            )

            final_bond_distance_a = (
                bonded_surface_atoms[0]["distance"]
                if bonded_surface_atoms
                else min(min_distance, min_distance_2)
            )
            bonded_desc = (
                ", ".join(
                    [
                        f"{bond['adsorbate_atom']}-{bond['symbol']}({bond['distance']}Å)"
                        for bond in bonded_surface_atoms
                    ]
                )
                if bonded_surface_atoms
                else "None"
            )

            planned_symbols = sorted(plan_solution.get("surface_binding_atoms", []))
            actual_symbols = sorted([atom["symbol"] for atom in bonded_surface_atoms])
            is_chemical_slip = False
            if planned_symbols and bonded_surface_atoms and planned_symbols != actual_symbols:
                is_chemical_slip = True
                logger.warning(
                    "Chemical site slip detected: planned=%s actual=%s",
                    planned_symbols,
                    actual_symbols,
                )

            analysis_message = (
                f"Most stable config adsorption energy: {e_ads:.4f} eV. "
                f"Target Atom 1: {target_atom_symbol} (from plan index {binding_atom_indices[0]}, "
                f"global index {target_atom_global_index}). "
                f"-> Nearest: {nearest_slab_atom_symbol} (Index {nearest_slab_atom_global_index}), "
                f"Distance: {round(min_distance, 3)} Å (Threshold: {round(bonding_cutoff, 3)}), "
                f"Bound: {is_bound_1}. "
                f"Target Atom 2: {second_atom_symbol} (from plan index {binding_atom_indices[1]}, "
                f"global index {second_atom_global_index}). "
                f"-> Nearest: {nearest_slab_atom_symbol_2} (Index {nearest_slab_atom_global_index_2}), "
                f"Distance: {round(min_distance_2, 3)} Å (Threshold: {round(bonding_cutoff_2, 3)}), "
                f"Bound: {is_bound_2}. Bonded Surface Atoms: {bonded_desc}. "
                f"Is Bound: {is_bound}. Reactivity Change Detected: {reaction_detected} "
                f"(Bond Changes: {bond_change_count}). Chemical Slip: {is_chemical_slip} "
                f"(Planned {planned_symbols} -> Actual {actual_symbols})."
            )

            result = {
                "status": "success",
                "message": analysis_message,
                "most_stable_energy_eV": e_ads,
                "bonded_surface_atoms": bonded_surface_atoms,
                "final_bond_distance_A": round(final_bond_distance_a, 3),
                "is_covalently_bound": is_bound,
                "atom_1": {
                    "symbol": target_atom_symbol,
                    "global_index": int(target_atom_global_index),
                    "distance_A": round(min_distance, 3),
                    "is_bound": bool(is_bound_1),
                },
                "atom_2": {
                    "symbol": second_atom_symbol,
                    "global_index": int(second_atom_global_index),
                    "distance_A": round(min_distance_2, 3),
                    "is_bound": bool(is_bound_2),
                },
                "reaction_detected": bool(reaction_detected),
                "bond_change_count": int(bond_change_count),
                "is_dissociated": bool(is_dissociated),
                "n_components": int(n_components),
                "site_analysis": {
                    "planned_site_type": planned_site_type,
                    "planned_connectivity": planned_connectivity,
                    "actual_site_type": actual_site_type,
                    "actual_connectivity": actual_connectivity,
                    "is_chemical_slip": is_chemical_slip,
                    "planned_symbols": planned_symbols,
                    "actual_symbols": actual_symbols,
                    "site_fingerprint": site_fingerprint,
                },
            }

        else:
            return json.dumps(
                {
                    "status": "error",
                    "message": (
                        "Analysis failed: unsupported number of binding indices "
                        f"{num_binding_indices}."
                    ),
                }
            )

        site_label = actual_site_type if actual_site_type != "unknown" else planned_site_type
        if planned_site_type != "unknown" and site_label != planned_site_type:
            site_label = f"{planned_site_type}_to_{site_label}"
        if is_dissociated:
            site_label += "_DISS"
        elif bond_change_count > 0:
            site_label += "_ISO"

        site_label = (
            site_label.replace(" ", "_")
            .replace("/", "-")
            .replace("(", "")
            .replace(")", "")
        )

        clean_smiles = sanitize_smiles_for_filename(original_smiles, strip_brackets=True)
        output_dir = ensure_output_dir(session_id)
        best_atoms_filename = output_dir / f"BEST_{clean_smiles}_{site_label}_E{e_ads:.3f}.xyz"

        try:
            write(str(best_atoms_filename), relaxed_atoms)
            logger.info("Saved best structure to %s", best_atoms_filename)
            result["best_structure_file"] = str(best_atoms_filename)
        except Exception as write_error:
            logger.error(
                "Unable to save best structure to %s: %s",
                best_atoms_filename,
                write_error,
            )

        return json.dumps(result)

    except Exception as exc:
        logger.error("Unexpected exception during relaxation analysis: %s", exc)
        logger.error("%s", traceback.format_exc())
        return json.dumps(
            {
                "status": "error",
                "message": f"Unexpected exception during relaxation analysis: {exc}",
            }
        )
