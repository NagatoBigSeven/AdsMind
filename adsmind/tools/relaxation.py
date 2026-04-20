"""Structure relaxation helpers."""

from __future__ import annotations

import ase
import numpy as np
from ase import units
from ase.constraints import FixAtoms
from ase.io import write
from ase.io.trajectory import Trajectory
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.neighborlist import natural_cutoffs
from ase.optimize import BFGS

from adsmind.tools.common import ensure_output_dir
from adsmind.tools.constants import FIXED_BOTTOM_FRACTION
from adsmind.utils.logger import get_logger

logger = get_logger(__name__)


def relax_atoms(
    atoms_list: list,
    slab_indices: list,
    calculator,
    session_id: str,
    relax_top_n: int = 1,
    fmax: float = 0.05,
    steps: int = 500,
    md_steps: int = 20,
    md_temp: float = 150.0,
    relaxation_mode: str = "fast",
) -> str:
    """Relax a list of atomic structures using an ASE-compatible calculator."""
    n_relax_top_n = relax_top_n

    if relaxation_mode == "standard" and len(atoms_list) > 0 and len(slab_indices) > 0:
        reference_atoms = atoms_list[0]
        slab_z_coords = reference_atoms.positions[slab_indices, 2]
        z_min, z_max = slab_z_coords.min(), slab_z_coords.max()
        z_threshold = z_min + (z_max - z_min) * FIXED_BOTTOM_FRACTION
        fixed_indices = [
            idx
            for idx in slab_indices
            if reference_atoms.positions[idx, 2] < z_threshold
        ]
        logger.info(
            "STANDARD relaxation mode: fixing %s/%s bottom slab atoms (Z < %.2f Å)",
            len(fixed_indices),
            len(slab_indices),
            z_threshold,
        )
        constraint = FixAtoms(indices=fixed_indices)
    else:
        if relaxation_mode != "fast":
            logger.warning(
                "Unknown relaxation_mode '%s', defaulting to 'fast'",
                relaxation_mode,
            )
        constraint = FixAtoms(indices=slab_indices)

    def _get_bond_change_count(initial, final):
        if len(initial) != len(final):
            return 0
        radii = np.array(natural_cutoffs(initial, mult=1.25))
        cutoff_mat = radii[:, None] + radii[None, :]
        d_initial = initial.get_all_distances(mic=True)
        d_final = final.get_all_distances(mic=True)

        symbols = initial.get_chemical_symbols()
        is_h = np.array([symbol == "H" for symbol in symbols])
        mask = is_h[:, None] & is_h[None, :]
        np.fill_diagonal(d_initial, 99.0)
        np.fill_diagonal(d_final, 99.0)

        bonds_initial = (d_initial < cutoff_mat) & (~mask)
        bonds_final_loose = (d_final < cutoff_mat * 1.5) & (~mask)
        bonds_final_strict = (d_final < cutoff_mat) & (~mask)

        broken = bonds_initial & (~bonds_final_loose)
        formed = (~bonds_initial) & bonds_final_strict
        return int(np.sum(np.triu(broken | formed)))

    logger.info(
        "Evaluation phase: evaluating %s configurations (MD warmup + SP energy)",
        len(atoms_list),
    )
    evaluated_configs = []
    for index, atoms in enumerate(atoms_list):
        atoms.calc = calculator
        atoms.set_constraint(constraint)

        max_force = np.max(np.linalg.norm(atoms.get_forces(), axis=1))
        if max_force > 200.0:
            logger.warning(
                "Skipping structure %s: initial force too high (max_force=%.2f eV/Å)",
                index + 1,
                max_force,
            )
            continue

        if md_steps > 0:
            MaxwellBoltzmannDistribution(atoms, temperature_K=md_temp)
            dyn_md = Langevin(
                atoms,
                1 * units.fs,
                temperature_K=md_temp,
                friction=0.01,
            )
            dyn_md.run(md_steps)

        energy = atoms.get_potential_energy()
        if (not np.isfinite(energy)) or energy < -2000.0:
            logger.warning(
                "Skipping structure %s: abnormal energy %.2f eV, suspected collapse",
                index + 1,
                energy,
            )
            continue

        logger.info(
            "Evaluating structure %s/%s: energy after warmup = %.4f eV",
            index + 1,
            len(atoms_list),
            energy,
        )
        evaluated_configs.append((energy, index, atoms.copy()))

    if not evaluated_configs:
        raise ValueError("Evaluation phase failed to evaluate any configurations.")

    evaluated_configs.sort(key=lambda item: item[0])

    if n_relax_top_n > len(evaluated_configs):
        logger.warning(
            "Requested top %s relaxations, but only %s configs are available. Relaxing all.",
            n_relax_top_n,
            len(evaluated_configs),
        )
        n_relax_top_n = len(evaluated_configs)

    configs_to_relax = evaluated_configs[:n_relax_top_n]
    logger.info(
        "Evaluation complete. Relaxing best %s of %s configurations.",
        n_relax_top_n,
        len(atoms_list),
    )

    output_dir = ensure_output_dir(session_id)
    traj_file = output_dir / "relaxation.traj"
    traj = Trajectory(str(traj_file), "w")
    final_structures = []

    for index, (initial_energy, original_index, atoms) in enumerate(configs_to_relax):
        logger.info(
            "Relaxing best structure %s/%s (original index %s, initial energy %.4f eV)",
            index + 1,
            n_relax_top_n,
            original_index,
            initial_energy,
        )

        atoms.calc = calculator
        atoms.set_constraint(constraint)

        adsorbate_indices = list(range(len(slab_indices), len(atoms)))
        initial_adsorbate = atoms.copy()[adsorbate_indices]

        logger.info("Optimization (BFGS): fmax=%s, steps=%s", fmax, steps)
        dyn_opt = BFGS(atoms, trajectory=None, logfile=None)
        dyn_opt.attach(lambda: traj.write(atoms), interval=1)
        dyn_opt.run(fmax=fmax, steps=steps)

        final_adsorbate = atoms.copy()[adsorbate_indices]
        bond_change_count = _get_bond_change_count(initial_adsorbate, final_adsorbate)
        atoms.info["bond_change_count"] = bond_change_count
        logger.info("Bond integrity check detected %s bond changes", bond_change_count)

        final_energy = atoms.get_potential_energy()
        final_forces = atoms.get_forces()
        logger.info(
            "Best structure %s relaxation complete. Final energy: %.4f eV",
            index + 1,
            final_energy,
        )

        atoms.results = {"energy": final_energy, "forces": final_forces}
        final_structures.append(atoms)

    traj.close()

    final_traj_file = output_dir / "final.xyz"
    try:
        write(str(final_traj_file), final_structures)
    except Exception as exc:
        logger.error("Failed to write final relaxed structures: %s", exc)
        raise

    logger.info(
        "Relaxation complete. Full trajectory: %s | Final structures (%s): %s",
        traj_file,
        len(final_structures),
        final_traj_file,
    )
    return str(final_traj_file)


def save_ase_atoms(atoms: ase.Atoms, filename: str) -> str:
    """Persist an ASE atoms object under outputs/ if a relative path is used."""
    output_root = ensure_output_dir()
    target_path = output_root / filename if not filename.startswith("outputs/") else filename

    try:
        write(str(target_path), atoms)
        logger.info("Saved structure to %s", target_path)
        return f"Saved to {target_path}"
    except Exception as exc:
        logger.error("Unable to save Atoms to %s: %s", target_path, exc)
        raise
