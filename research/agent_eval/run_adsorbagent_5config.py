"""Run Adsorb-Agent under the AdsMind 5-configuration protocol.

This script is intended to be executed inside the modified CatalystAIgent
environment on the remote server. It reads AdsMind benchmark slabs directly,
asks the Adsorb-Agent planner for one adsorption motif, generates at most five
initial configurations from that motif, and relaxes them with MACE-MP-0 small.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pickle
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from ase.constraints import FixAtoms
from ase.io import read


FIXED_BOTTOM_FRACTION = 1.0 / 3.0
SITE_TYPES = {"ontop", "bridge", "hollow"}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def case_sort_key(row: dict[str, str]) -> tuple[int, str]:
    raw = str(row.get("case_id", ""))
    try:
        return int(raw), raw
    except ValueError:
        return 999999, raw


def parse_cases(raw: str, rows: list[dict[str, str]]) -> set[str]:
    all_cases = {str(row["case_id"]).zfill(len(str(row["case_id"]))) for row in rows}
    if raw.lower() == "all":
        return all_cases
    selected = {item.strip() for item in raw.split(",") if item.strip()}
    width = max(len(str(row["case_id"])) for row in rows)
    return {item.zfill(width) for item in selected}


def clean_site_type(value: str) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if text in SITE_TYPES:
        return text
    if "top" in text:
        return "ontop"
    if "bridge" in text or text.startswith("brg"):
        return "bridge"
    if "hollow" in text or "fcc" in text or "hcp" in text:
        return "hollow"
    raise ValueError(f"Unsupported Adsorb-Agent site type: {value!r}")


def clean_element_symbols(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        raw_values = re.split(r"[,;/ ]+", values)
    else:
        raw_values = list(values)

    symbols: list[str] = []
    for raw in raw_values:
        match = re.search(r"\b([A-Z][a-z]?)\b", str(raw))
        if match:
            symbols.append(match.group(1))
    return symbols


def bottom_fixed_indices(atoms) -> list[int]:
    tags = atoms.get_tags()
    slab_indices = [idx for idx, tag in enumerate(tags) if tag in (0, 1)]
    if not slab_indices:
        slab_indices = list(range(len(atoms)))
    z = atoms.positions[slab_indices, 2]
    threshold = float(z.min() + (z.max() - z.min()) * FIXED_BOTTOM_FRACTION)
    return [idx for idx in slab_indices if atoms.positions[idx, 2] < threshold]


def derive_surface_label(row: dict[str, str]) -> str:
    if row.get("surface_formula"):
        return row["surface_formula"]
    slab_file = Path(row.get("slab_file", "")).stem
    pieces = slab_file.split("_")
    if pieces and pieces[0].isdigit():
        pieces = pieces[1:]
    if pieces and pieces[-1].isdigit():
        pieces = pieces[:-1]
    return "_".join(pieces) or slab_file


def load_adsorbate_index(path: Path) -> dict[str, Path]:
    rows = load_csv(path)
    return {row["smiles"]: path.parent / row["adsorbate_file"] for row in rows}


def save_pickle(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def save_text(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(payload), encoding="utf-8")


def save_case_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)


def setup_catalyst_imports(catalyst_root: Path) -> None:
    sys.path.insert(0, str(catalyst_root))
    sys.path.insert(0, str(catalyst_root / "fairchem-forked" / "src"))
    os.chdir(catalyst_root)


def run_case(
    *,
    row: dict[str, str],
    input_root: Path,
    output_root: Path,
    config_root: Path,
    adsorbate_files: dict[str, Path],
    catalyst_modules: dict[str, Any],
    max_configs: int,
    max_critic_loops: int,
    random_ratio: float,
    skip_existing: bool,
) -> dict[str, Any]:
    started = time.perf_counter()
    case_id = str(row["case_id"]).zfill(len(str(row["case_id"])))
    surface_label = derive_surface_label(row)
    smiles = row["smiles"]
    case_name = f"{case_id}_{surface_label}_{row.get('adsorbate_name') or smiles}"
    case_name = re.sub(r"[^A-Za-z0-9_.+-]+", "_", case_name).strip("_")
    case_dir = output_root / case_name
    traj_dir = case_dir / "traj"
    result_path = case_dir / "result.pkl"

    if skip_existing and result_path.exists() and traj_dir.exists() and list(traj_dir.glob("*.traj")):
        return {
            "case_id": case_id,
            "case_name": case_name,
            "status": "skipped_existing",
            "traj_count": len(list(traj_dir.glob("*.traj"))),
            "wall_clock_sec": 0.0,
            "error": "",
        }

    case_dir.mkdir(parents=True, exist_ok=True)
    traj_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "config_name": case_name,
        "system_info": {
            "ads_smiles": smiles,
            "bulk_symbol": surface_label,
            "bulk_id": row.get("ocd_id") or row.get("benchmark_id") or "",
            "miller": row.get("miller_index", ""),
            "shift": "",
            "top": "",
            "system_id": None,
            "num_site": max_configs,
            "random_ratio": random_ratio,
            "slab_file": row.get("slab_file", ""),
            "user_request": row.get("user_request", ""),
        },
    }
    save_case_config(config_root / f"{case_name}.yaml", config)
    save_case_config(case_dir / f"{case_name}.yaml", config)

    try:
        slab_path = input_root / row["slab_file"]
        adsorbate_path = adsorbate_files[smiles]
        slab_atoms = read(slab_path)
        slab_atoms.set_constraint(FixAtoms(indices=bottom_fixed_indices(slab_atoms)))
        adsorbate_atoms = read(adsorbate_path)

        observations = (
            f"The adsorbate is {smiles} and the catalyst surface is {surface_label}. "
            f"{row.get('user_request', '')}".strip()
        )

        aa = catalyst_modules["adsorb_agent"]
        Bulk = catalyst_modules["Bulk"]
        Slab = catalyst_modules["Slab"]
        Adsorbate = catalyst_modules["Adsorbate"]
        AdsorbateSlabConfig = catalyst_modules["AdsorbateSlabConfig"]
        ChatOpenAI = catalyst_modules["ChatOpenAI"]
        OpenAICallbackHandler = catalyst_modules["OpenAICallbackHandler"]
        relax_adslab = catalyst_modules["relax_adslab"]

        token_callback = OpenAICallbackHandler() if OpenAICallbackHandler is not None else None
        callbacks = [token_callback] if token_callback is not None else None
        llm_model = ChatOpenAI(model="gpt-5.4-2026-03-05", callbacks=callbacks)

        reasoning_questions = aa.load_text_file(
            str(catalyst_modules["catalyst_root"] / "reasoning" / "reasoning.txt")
        )
        knowledge_statements = aa.load_text_file(
            str(catalyst_modules["catalyst_root"] / "reasoning" / "knowledge.txt")
        )

        reasoning_adapter = aa.info_reasoning_adapter(model=llm_model)
        reasoning_result = reasoning_adapter.invoke(
            {"observations": observations, "reasoning": reasoning_questions}
        )

        solution_result = None
        surface_critic_valid = False
        adsorbate_critic_valid = False
        critic_loop_count = 0
        while not (surface_critic_valid and adsorbate_critic_valid):
            solution_adapter = aa.solution_planner(model=llm_model)
            solution_result = solution_adapter.invoke(
                {
                    "observations": observations,
                    "adapter_solution_reasoning": reasoning_result.adapted_prompts,
                }
            )

            surface_critic_adapter = aa.surface_critic(model=llm_model)
            surface_critic_result = surface_critic_adapter.invoke(
                {
                    "observations": observations,
                    "adsorption_site_type": solution_result.adsorption_site_type,
                    "binding_atoms_on_surface": solution_result.binding_atoms_on_surface,
                    "knowledge": knowledge_statements,
                }
            )
            adsorbate_critic_adapter = aa.adsorbate_critic(model=llm_model)
            adsorbate_critic_result = adsorbate_critic_adapter.invoke(
                {
                    "observations": observations,
                    "binding_atoms_in_adsorbate": solution_result.binding_atoms_in_adsorbate,
                    "orientation_of_adsorbate": solution_result.orientation_of_adsorbate,
                    "knowledge": knowledge_statements,
                }
            )
            surface_critic_valid = surface_critic_result.solution == 1
            adsorbate_critic_valid = adsorbate_critic_result.solution == 1
            critic_loop_count += 1
            if critic_loop_count >= max_critic_loops:
                break

        if solution_result is None:
            raise RuntimeError("Adsorb-Agent did not return a solution.")

        site_type = clean_site_type(solution_result.adsorption_site_type)
        site_atoms = clean_element_symbols(solution_result.binding_atoms_on_surface)
        if not site_atoms:
            raise ValueError(f"No usable surface element symbols from {solution_result.binding_atoms_on_surface!r}")

        index_adapter = aa.binding_indexer(model=llm_model)
        index_result = index_adapter.invoke(
            {"observations": solution_result.text, "atomic_numbers": adsorbate_atoms.numbers}
        )
        binding_indices = [int(idx) for idx in index_result.solution]
        if not binding_indices or max(binding_indices) >= len(adsorbate_atoms) or min(binding_indices) < 0:
            raise ValueError(
                f"Invalid adsorbate binding indices {binding_indices} for {len(adsorbate_atoms)} atoms"
            )

        bulk = Bulk(bulk_atoms=slab_atoms.copy())
        # The CatalystAIgent fairchem fork's Slab.from_atoms currently passes a
        # pymatgen Structure into Slab.__init__, while __init__ expects ASE
        # Atoms. Construct Slab directly to keep the AdsMind slab unchanged.
        slab = Slab(bulk=bulk, slab_atoms=slab_atoms)
        adsorbate = Adsorbate(
            adsorbate_atoms=adsorbate_atoms,
            adsorbate_binding_indices=np.array(binding_indices),
        )

        cutoff_multiplier = 1.1
        adslabs = []
        while not adslabs and cutoff_multiplier <= 1.300001:
            try:
                adslabs_config = AdsorbateSlabConfig(
                    slab,
                    adsorbate,
                    num_sites=max_configs,
                    num_augmentations_per_site=1,
                    mode="llm-guided",
                    site_type=site_type,
                    site_atoms=site_atoms,
                    random_ratio=random_ratio,
                    cutoff_multiplier=cutoff_multiplier,
                )
                adslabs = list(adslabs_config.atoms_list)[:max_configs]
            except Exception:
                adslabs = []
            cutoff_multiplier += 0.05

        result_dict: dict[str, Any] = {
            "system": [str(slab_path), smiles, surface_label],
            "initial_solution": {
                "site_type": site_type,
                "site_atoms": site_atoms,
                "num_site_atoms": len(site_atoms),
                "ads_bind_atoms": list(solution_result.binding_atoms_in_adsorbate),
                "adsorbate_binding_indices": binding_indices,
                "orient": solution_result.orientation_of_adsorbate,
                "reasoning": solution_result.reasoning,
            },
            "critic_loop_count": critic_loop_count,
            "config_no_count": len(adslabs),
            "cutoff_multiplier": cutoff_multiplier,
            "max_config_budget": max_configs,
            "random_ratio": random_ratio,
        }

        if token_callback is not None:
            result_dict.update(
                {
                    "llm_token_count": token_callback.total_tokens,
                    "llm_prompt_tokens": token_callback.prompt_tokens,
                    "llm_completion_tokens": token_callback.completion_tokens,
                    "llm_successful_requests": token_callback.successful_requests,
                    "llm_total_cost_usd": token_callback.total_cost,
                }
            )

        if not adslabs:
            result_dict["error"] = "no_selected_configurations"
            save_pickle(result_path, result_dict)
            save_text(case_dir / "result.txt", result_dict)
            return {
                "case_id": case_id,
                "case_name": case_name,
                "status": "no_selected_configurations",
                "traj_count": 0,
                "wall_clock_sec": time.perf_counter() - started,
                "error": "no_selected_configurations",
            }

        relaxed_energies = []
        for idx, adslab in enumerate(adslabs):
            save_path = traj_dir / f"config_{idx}.traj"
            relaxed = relax_adslab(adslab, "mace-mp-0-small", str(save_path))
            relaxed_energies.append(float(relaxed.get_potential_energy()))

        min_idx = int(np.argmin(relaxed_energies))
        result_dict["min_energy"] = float(relaxed_energies[min_idx])
        result_dict["min_idx"] = min_idx
        save_pickle(result_path, result_dict)
        save_text(case_dir / "result.txt", result_dict)
        return {
            "case_id": case_id,
            "case_name": case_name,
            "status": "success",
            "traj_count": len(adslabs),
            "wall_clock_sec": time.perf_counter() - started,
            "error": "",
        }
    except Exception as exc:
        payload = {
            "system": [row.get("slab_file", ""), smiles, surface_label],
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "max_config_budget": max_configs,
        }
        save_pickle(result_path, payload)
        save_text(case_dir / "result.txt", payload)
        return {
            "case_id": case_id,
            "case_name": case_name,
            "status": "error",
            "traj_count": 0,
            "wall_clock_sec": time.perf_counter() - started,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalyst-root", required=True, type=Path)
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--adsorbate-index", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--config-root", required=True, type=Path)
    parser.add_argument("--cases", default="all")
    parser.add_argument("--max-configs", type=int, default=5)
    parser.add_argument("--max-critic-loops", type=int, default=8)
    parser.add_argument("--random-ratio", type=float, default=0.2)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    setup_catalyst_imports(args.catalyst_root.resolve())

    import adsorb_agent as aa  # type: ignore
    from adsorb_agent import OpenAICallbackHandler  # type: ignore
    from fairchem.data.oc.core import Adsorbate, AdsorbateSlabConfig, Bulk, Slab  # type: ignore
    from langchain_openai import ChatOpenAI  # type: ignore
    from utils import relax_adslab  # type: ignore

    catalyst_modules = {
        "adsorb_agent": aa,
        "OpenAICallbackHandler": OpenAICallbackHandler,
        "ChatOpenAI": ChatOpenAI,
        "Bulk": Bulk,
        "Slab": Slab,
        "Adsorbate": Adsorbate,
        "AdsorbateSlabConfig": AdsorbateSlabConfig,
        "relax_adslab": relax_adslab,
        "catalyst_root": args.catalyst_root.resolve(),
    }

    rows = sorted(load_csv(args.manifest), key=case_sort_key)
    selected = parse_cases(args.cases, rows)
    adsorbate_files = load_adsorbate_index(args.adsorbate_index)

    progress_path = args.output_root / "progress.csv"
    progress_fields = ["case_id", "case_name", "status", "traj_count", "wall_clock_sec", "error"]
    for row in rows:
        width = len(str(row["case_id"]))
        row["case_id"] = str(row["case_id"]).zfill(width)
        if row["case_id"] not in selected:
            continue
        progress = run_case(
            row=row,
            input_root=args.input_root,
            output_root=args.output_root,
            config_root=args.config_root,
            adsorbate_files=adsorbate_files,
            catalyst_modules=catalyst_modules,
            max_configs=args.max_configs,
            max_critic_loops=args.max_critic_loops,
            random_ratio=args.random_ratio,
            skip_existing=args.skip_existing,
        )
        append_csv(progress_path, progress, progress_fields)
        print(json.dumps(progress, ensure_ascii=False), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
