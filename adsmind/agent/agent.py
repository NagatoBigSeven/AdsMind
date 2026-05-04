import os
import argparse
import json
from typing import TypedDict, List, Optional, Dict, Any
import numpy as np
from rdkit import Chem
from dotenv import load_dotenv

# Calculator backend abstraction
from adsmind.calculators import get_backend
from adsmind.calculators.base import CalculatorConfig

# LLM backend abstraction
from adsmind.llms import get_llm_backend

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_core.output_parsers import JsonOutputParser

from adsmind.utils.logger import get_logger
from adsmind.agent.history import build_history_entry
from adsmind.utils.config import get_calculator_backend, get_llm_backend_name
from adsmind.agent.prompts import build_planner_prompt

# Initialize logger for this module
logger = get_logger(__name__)

DEFAULT_MAX_ATTEMPTS = 5

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    # Session isolation
    session_id: str  # UUID for file path isolation
    api_key: str     # API key for this session (not from global env)
    # LLM configuration
    llm_backend: str  # LLM backend name ("openai", "anthropic", "openrouter", etc.)
    llm_config: Optional[Dict[str, Any]]  # Optional LLM configuration overrides
    # Calculator configuration
    calculator_backend: str
    calculator_config: Optional[Dict[str, Any]]
    relaxation_config: Optional[Dict[str, Any]]
    # Reproducibility
    random_seed: Optional[int]  # Optional random seed for reproducible runs (None = not fixed)
    # Relaxation settings
    relaxation_mode: str  # "fast" (all slab fixed) or "standard" (bottom 1/3 fixed)
    # Experiment instrumentation
    total_input_tokens: int
    total_output_tokens: int
    enable_slip_feedback: bool
    enable_forbid: bool
    enable_termination: bool
    max_attempts: int
    validation_retry_count: int
    # Input data
    smiles: str
    slab_path: str
    surface_composition: Optional[List[str]]
    user_request: str
    # Planning
    plan: Optional[dict]
    validation_error: Optional[str]
    messages: List[BaseMessage]
    # Results
    analysis_json: Optional[str]
    history: List[str]
    attempt_records: List[Dict[str, Any]]
    best_result: Optional[dict]
    best_dissociated_result: Optional[dict]
    attempted_keys: List[str]
    available_sites_description: Optional[str]
    summary_report_file: Optional[str]
    best_configuration_png: Optional[str]
    iteration_energy_curve_png: Optional[str]
    visualization_error: Optional[str]

# --- 2. Setup Environment and LLM ---
load_dotenv()

# Note: API key is now passed via AgentState, not global env var
# This prevents key leakage between concurrent sessions

# Default LLM backend (can be overridden via environment variable)
DEFAULT_LLM_BACKEND = "openrouter"


def _read_usage_value(container: Any, *keys: str) -> int:
    """Return the first usable integer token count from dict/object metadata."""
    if container is None:
        return 0

    for key in keys:
        value = container.get(key) if isinstance(container, dict) else getattr(container, key, None)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def extract_token_usage(response: Any) -> tuple[int, int]:
    """Extract prompt/output token counts from LangChain response metadata."""
    usage_metadata = getattr(response, "usage_metadata", None)
    prompt_tokens = _read_usage_value(
        usage_metadata,
        "input_tokens",
        "prompt_token_count",
        "prompt_tokens",
    )
    output_tokens = _read_usage_value(
        usage_metadata,
        "output_tokens",
        "candidates_token_count",
        "completion_tokens",
    )

    response_metadata = getattr(response, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") if isinstance(response_metadata, dict) else {}
    prompt_tokens = prompt_tokens or _read_usage_value(token_usage, "prompt_tokens", "input_tokens")
    output_tokens = output_tokens or _read_usage_value(
        token_usage,
        "completion_tokens",
        "output_tokens",
    )
    return prompt_tokens, output_tokens


def get_max_attempts(state: AgentState) -> int:
    """Return the hard attempt cap for the current run."""
    try:
        value = int(state.get("max_attempts", DEFAULT_MAX_ATTEMPTS))
    except (TypeError, ValueError):
        value = DEFAULT_MAX_ATTEMPTS
    return max(1, value)


def _coalesce_override(overrides: Optional[Dict[str, Any]], key: str, default: Any) -> Any:
    """Return a runtime override only when it is explicitly non-null."""
    if not overrides:
        return default
    value = overrides.get(key, default)
    return default if value is None else value


def _apply_calculator_overrides(
    calc_config: CalculatorConfig,
    overrides: Optional[Dict[str, Any]],
) -> CalculatorConfig:
    """Apply experiment-time calculator overrides on top of backend defaults."""
    if not overrides:
        return calc_config

    for key, value in overrides.items():
        if value is None:
            continue
        if key == "extra_options" and isinstance(value, dict):
            calc_config.extra_options.update(value)
        elif hasattr(calc_config, key):
            setattr(calc_config, key, value)
    return calc_config


def get_llm(api_key: str, backend_name: str = None, llm_config: dict = None):
    """
    Create an LLM instance using the configured backend.
    
    This function uses a factory pattern to support multiple LLM backends:
    - openai: OpenAI GPT API (official endpoint)
    - anthropic: Anthropic Claude API (official endpoint)
    - openrouter: OpenRouter API (multiple providers)
    - ollama: Local Ollama service
    - huggingface: Local HuggingFace Transformers
    
    Args:
        api_key: API key for cloud backends (ignored for local backends)
        backend_name: Backend name (defaults to ADSMIND_LLM_BACKEND env var or "openrouter")
        llm_config: Optional configuration overrides
        
    Returns:
        LangChain-compatible chat model instance
    """
    # Determine backend
    if backend_name is None:
        backend_name = get_llm_backend_name()
    
    # Get backend instance
    backend = get_llm_backend(backend_name)
    
    # Validate API key for cloud backends
    if backend.requires_api_key and not api_key:
        raise ValueError(
            f"{backend_name.capitalize()} backend requires an API key. "
            f"Please enter your API key in the app or set the appropriate environment variable."
        )
    
    # Get default config
    config = backend.get_default_config(api_key=api_key)
    
    # Apply overrides from llm_config
    if llm_config:
        for key, value in llm_config.items():
            if key == "extra_options" and isinstance(value, dict):
                config.extra_options.update(value)
            elif hasattr(config, key):
                setattr(config, key, value)
            else:
                # Backend-specific options go into extra_options
                config.extra_options[key] = value
    
    logger.info(f"Using LLM backend: {backend_name} (model: {config.model})")
    return backend.get_chat_model(config)

def make_plan_key(plan_json: Optional[dict]) -> Optional[str]:
    if not plan_json or not isinstance(plan_json, dict):
        return None
    try:
        solution = plan_json.get("solution", {}) or {}
        site_type = solution.get("site_type", "") or ""
        surf_atoms = solution.get("surface_binding_atoms", []) or []
        ads_indices = solution.get("adsorbate_binding_indices", []) or []
        touch_sphere = solution.get("touch_sphere_size", 2)
        ads_type = plan_json.get("adsorbate_type", "Molecule")

        # Ensure both are lists, otherwise return None (no exception raised)
        if not isinstance(surf_atoms, list) or not isinstance(ads_indices, list):
            return None

        # Convert to string, preserving order to distinguish heteronuclear dual-point adsorption direction (e.g., Mo-Pd vs Pd-Mo)
        surf_atoms_str = ",".join(str(s) for s in surf_atoms)
        ads_indices_str = ",".join(str(i) for i in ads_indices)

        key = f"{site_type}|{surf_atoms_str}|{ads_indices_str}|{ads_type}|{float(touch_sphere):.1f}"
        return key
    except Exception as e:
        logger.warning(f"make_plan_key failed: {e}")
        return None


def get_valid_binding_indices(mol: Chem.Mol) -> set[int]:
    """Return planner-visible binding indices for the current adsorbate.

    The planner normally sees heavy-atom indices only. Single-atom species such as
    ``[H]`` have no heavy atoms, so we fall back to all atom indices in that case.
    """
    heavy_atom_indices = {
        atom.GetIdx() for atom in mol.GetAtoms() if atom.GetSymbol() != "H"
    }
    if heavy_atom_indices:
        return heavy_atom_indices
    return {atom.GetIdx() for atom in mol.GetAtoms()}

# --- 3. Define LangGraph Nodes ---
def pre_processor_node(state: AgentState) -> dict:
    logger.info("Calling Pre-Processor Node")
    from adsmind.tools.tools import analyze_surface_sites

    try:
        analysis = analyze_surface_sites(state["slab_path"])
        return {
            "surface_composition": analysis["surface_composition"],
            "available_sites_description": analysis["available_sites_description"]
        }
    except Exception as e:
        error_message = f"Error: Unable to read Slab file '{state['slab_path']}': {e}"
        logger.info(f"Validation Failed: {error_message}")
        return {
            "validation_error": error_message,
            "surface_composition": None,
            "available_sites_description": None
        }

def solution_planner_node(state: AgentState) -> dict:
    logger.info("Calling Planner Node")
    from adsmind.tools.tools import get_atom_index_menu

    llm = get_llm(
        state["api_key"],
        backend_name=state.get("llm_backend"),
        llm_config=state.get("llm_config")
    )
    messages = []

    try:
        atom_menu_json = get_atom_index_menu(state["smiles"])
        if "error" in atom_menu_json:
            raise ValueError(atom_menu_json)
    except Exception as e:
        logger.error(f"fatal error: Unable to generate atom menu for SMILES {state['smiles']}: {e}")
        return {
            "validation_error": f"False, fatal error: Unable to generate atom menu for SMILES {state['smiles']}: {e}"
        }
    
    prompt_input = {
        "smiles": state["smiles"],
        "slab_path": state["slab_path"],
        "surface_composition": state.get("surface_composition", "Unknown"),
        "user_request": state["user_request"],
        "history": "\n".join(state["history"]) if state.get("history") else "None",
        "max_attempts": get_max_attempts(state),
        "autoadsorbate_context": atom_menu_json,
        "available_sites_description": state.get("available_sites_description", "None"),
        "enable_slip_feedback": state.get("enable_slip_feedback", True),
        "enable_forbid": state.get("enable_forbid", True),
        "enable_termination": state.get("enable_termination", True),
    }
    planner_prompt = build_planner_prompt(**prompt_input)
    
    if state.get("validation_error"):
        messages.append(HumanMessage(content=planner_prompt))
        messages.append(AIMessage(content=json.dumps(state.get("plan", "{}"))))
        messages.append(HumanMessage(content=f"Your plan has logical errors: {state['validation_error']}. Please replan."))
    else:
        if state.get("history"):
            logger.info("Planner: Detected failure history, retrying...")
        messages.append(HumanMessage(content=planner_prompt))

    response = llm.invoke(messages)
    input_tokens, output_tokens = extract_token_usage(response)
    total_input_tokens = state.get("total_input_tokens", 0) + input_tokens
    total_output_tokens = state.get("total_output_tokens", 0) + output_tokens
    
    try:
        parser = JsonOutputParser()

        content_str = response.content
        if content_str.startswith("```json"):
            content_str = content_str[7:-3].strip()
        
        plan_json = parser.parse(content_str)
        logger.info("Planner Plan Generated")
        return {
            "plan": plan_json,
            "messages": [AIMessage(content=response.content)],
            "validation_error": None,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }
    except Exception as e:
        logger.error(f"Planner Output JSON Parse Failed: {e}")
        logger.info(f"Raw Output: {response.content}")
        return {
            "plan": None,
            "validation_error": f"False, Planner output format error: {e}. Please output strictly in JSON format.",
            "messages": [AIMessage(content=response.content)],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }

def plan_validator_node(state: AgentState) -> dict:
    """ Node 2: Python Validator """
    logger.info("Calling Python Validator Node")
    validation_retry_count = int(state.get("validation_retry_count", 0) or 0)

    def fail_validation(error: str, *, clear_plan: bool = False) -> dict:
        logger.info(f"Validation Failed: {error}")
        payload = {
            "validation_error": error,
            "validation_retry_count": validation_retry_count + 1,
        }
        if clear_plan:
            payload["plan"] = None
        return payload

    try:
        # Use state["smiles"] (from initial input) instead of anything in the plan
        mol = Chem.MolFromSmiles(state["smiles"])
        if not mol:
            raise ValueError(
                "RDKit returned None. SMILES might be invalid or contain valences RDKit cannot handle."
            )
    except Exception as e:
        error = f"False, Base SMILES string '{state['smiles']}' cannot be parsed by RDKit. This is an unrecoverable error. Please check SMILES. Error: {e}"
        # This is a fatal error; we should stop retrying.
        # We notify the router by setting a special validation_error
        # Note: Ideally, the graph should have a "terminal_failure" state,
        # but currently we can only return to the planner and expect it to stop after N attempts.
        return fail_validation(error, clear_plan=True) # Clear plan

    plan_json = state.get("plan")
    if plan_json is None:
        return fail_validation(
            state.get("validation_error", "False, Planner node failed to generate valid JSON.")
        )
    if "solution" not in plan_json:
        error = "False, Plan JSON missing 'solution' key."
        return fail_validation(error)
    
    adsorbate_type = plan_json.get("adsorbate_type")
    if adsorbate_type not in ["Molecule", "ReactiveSpecies"]:
        error = (
            "False, Plan JSON missing or invalid `adsorbate_type` field "
            "(must be 'Molecule' or 'ReactiveSpecies')."
        )
        return fail_validation(error)

    solution = plan_json.get("solution", {})
    if not solution:
        error = "False, Plan JSON missing or malformed ('solution' key is empty)."
        return fail_validation(error)
    if solution.get("action") == "terminate" and not state.get("enable_termination", True):
        error = (
            "False, Termination is disabled for this run. "
            "Please provide another adsorption plan instead of terminate."
        )
        return fail_validation(error)

    if solution.get("action") == "terminate":
        logger.error("Planner decided to terminate (converged or no more plans)")
        return {"validation_error": None, "validation_retry_count": validation_retry_count}  # Pass directly

    site_type = solution.get("site_type", "")
    surf_atoms = solution.get("surface_binding_atoms", [])
    ads_indices = solution.get("adsorbate_binding_indices", [])
    valid_binding_indices = get_valid_binding_indices(mol)
    if not isinstance(ads_indices, list):
        error = "False, Plan JSON field 'adsorbate_binding_indices' must be a list."
        return fail_validation(error)
    if any(not isinstance(idx, int) for idx in ads_indices):
        error = (
            "False, Rule 2: Python check failed. "
            "'adsorbate_binding_indices' must contain only integers."
        )
        return fail_validation(error)
    if len(set(ads_indices)) != len(ads_indices):
        error = (
            "False, Rule 2: Python check failed. "
            "'adsorbate_binding_indices' must not repeat the same atom index."
        )
        return fail_validation(error)
    invalid_indices = [idx for idx in ads_indices if idx not in valid_binding_indices]
    if invalid_indices:
        valid_indices_text = sorted(valid_binding_indices)
        error = (
            "False, Rule 2: Python check failed. "
            f"'adsorbate_binding_indices' must refer to planner-visible atoms {valid_indices_text}, "
            f"but got invalid indices {invalid_indices}."
        )
        return fail_validation(error)
    if site_type == "ontop" and len(ads_indices) != 1:
        error = f"False, Rule 2: Python check failed. site_type 'ontop' must pair with 1 index (end-on), but got {len(ads_indices)}."
        return fail_validation(error)
    if site_type == "bridge" and len(ads_indices) not in [1, 2]:
        error = f"False, Rule 2: Python check failed. site_type 'bridge' must pair with 1 (end-on) or 2 (side-on) indices, but got {len(ads_indices)}."
        return fail_validation(error)
    if site_type == "hollow" and len(ads_indices) not in [1, 2]:
        error = f"False, Rule 2: Python check failed. site_type 'hollow' must pair with 1 (end-on) or 2 (side-on) indices, but got {len(ads_indices)}."
        return fail_validation(error)
    if not isinstance(surf_atoms, list):
        error = "False, Plan JSON field 'surface_binding_atoms' must be a list."
        return fail_validation(error)
    if site_type == "ontop" and len(surf_atoms) != 1:
        error = (
            "False, Rule 2b: 'ontop' site requires surface_binding_atoms length of 1, "
            f"but got {len(surf_atoms)}."
        )
        return fail_validation(error)
    if site_type == "bridge" and len(surf_atoms) not in [1, 2]:
        error = (
            "False, Rule 2b: 'bridge' site requires surface_binding_atoms length of 1 or 2, "
            f"but got {len(surf_atoms)}."
        )
        return fail_validation(error)
    if site_type == "hollow" and len(surf_atoms) < 3:
        error = (
            "False, Rule 2b: 'hollow' site requires surface_binding_atoms to have at least 3 elements, "
            f"but got {len(surf_atoms)}."
        )
        return fail_validation(error)
    
    try:
        attempted_keys = state.get("attempted_keys", [])
        if not isinstance(attempted_keys, list):
            attempted_keys = []
        key = make_plan_key(plan_json)
        if key is not None and key in attempted_keys:
            error = (
                "False, This plan has already been attempted in the (site_type, surface_binding_atoms, adsorbate_binding_indices) space. "
                "Please plan a different combination."
            )
            return fail_validation(error)
    except Exception as e_dup:
        logger.warning(f"Exception during Duplicate-check: {e_dup}")

    logger.info("Validation Succeeded ")
    return {"validation_error": None, "validation_retry_count": validation_retry_count}

def tool_executor_node(state: AgentState) -> dict:
    """ Node 4: Tool Executor """
    logger.info("Calling Tool Executor Node")
    from ase import units
    from ase.constraints import FixAtoms
    from ase.io import read
    from ase.md.langevin import Langevin
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
    from ase.optimize import BFGS
    import torch
    from adsmind.tools.tools import (
        read_atoms_object,
        prepare_slab,
        create_fragment_from_plan,
        populate_surface_with_fragment,
        relax_atoms,
        analyze_relaxation_results,
    )
    
    # Set random seeds for reproducibility if specified
    random_seed = state.get("random_seed")
    if random_seed is not None:
        import random
        random.seed(random_seed)
        np.random.seed(random_seed)
        torch.manual_seed(random_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(random_seed)
        logger.info(f"Random seed set to {random_seed} for reproducibility")
    
    plan_json = state.get("plan", {})
    plan_solution = plan_json.get("solution", {})

    if not plan_solution:
        error_message = "Tool Executor Failed: 'plan' missing 'solution' dictionary."
        logger.error(f"{error_message}")
        return {
            "messages": [ToolMessage(content=error_message, tool_call_id="tool_executor")],
            "analysis_json": json.dumps({"status": "error", "message": error_message})
        }

    slab_path = state["slab_path"]
    tool_logs = []
    analysis_json = None

    new_best_molecular = state.get("best_result")
    new_best_dissociated = state.get("best_dissociated_result")
    
    try:
        # 1. Read original Slab
        raw_slab_atoms = read_atoms_object(slab_path)
        tool_logs.append(f"Success: Read slab atoms from {slab_path}.")

        # 2. Prepare Slab before any energy calculation
        final_slab_atoms, is_expanded = prepare_slab(raw_slab_atoms)
        if is_expanded:
            tool_logs.append("Note: Slab was automatically expanded (2x2) for physical accuracy.")
        
        # 3. Initialize Calculator via Backend Abstraction
        try:
            # Get the calculator backend (defaults to MACE)
            backend_name = state.get("calculator_backend") or get_calculator_backend()
            backend = get_backend(backend_name)
            
            # Check GPU availability
            has_cuda = torch.cuda.is_available()
            
            # Get platform-specific configuration from backend
            calc_config = backend.get_default_config(has_gpu=has_cuda)
            calc_config = _apply_calculator_overrides(
                calc_config,
                state.get("calculator_config"),
            )
            relax_params = backend.get_default_relaxation_params(has_gpu=has_cuda)
            
            # Extract parameters for use in this function
            relax_overrides = state.get("relaxation_config") or {}
            opt_fmax = float(_coalesce_override(relax_overrides, "fmax", relax_params.fmax))
            opt_steps = int(_coalesce_override(relax_overrides, "steps", relax_params.steps))
            md_steps = int(_coalesce_override(relax_overrides, "md_steps", relax_params.md_steps))
            md_temp = float(_coalesce_override(relax_overrides, "md_temp", relax_params.md_temp))
            
            # Get calculator instance
            temp_calc = backend.get_calculator(calc_config)
            
            # Log configuration for debugging
            logger.info(
                f"Using {backend.name} backend: device={calc_config.device}, "
                f"model={calc_config.model}, precision={calc_config.precision}"
            )

        except Exception as e_calc:
            raise ValueError(f"Failed to initialize calculator: {e_calc}")

        # 4. Calculate E_surface
        try:
            e_surf_atoms = final_slab_atoms.copy()
            e_surf_atoms.calc = temp_calc

            # *** Apply constraints EXACTLY as in relax_atoms ***
            # tools.py::relax_atoms fixes *ALL* surface atoms.
            constraint = FixAtoms(indices=list(range(len(e_surf_atoms))))
            e_surf_atoms.set_constraint(constraint)

            logger.info("Calculating single point energy of bare surface (all atoms fixed)")

            E_surface = e_surf_atoms.get_potential_energy() # This is now a single point energy
            tool_logs.append(f"Success: E_surface = {E_surface:.4f} eV.")
            
        except Exception as e_surf_err:
            raise ValueError(f"Failed to calculate E_surface: {e_surf_err}")

        # 5. Create Fragment
        fragment_object = create_fragment_from_plan(
            original_smiles=state["smiles"],
            binding_atom_indices=plan_solution.get("adsorbate_binding_indices"),
            plan_dict=plan_json,
            to_initialize=plan_solution.get("conformers_per_site_cap", 4)
        )
        tool_logs.append(f"Success: Created fragment object from plan (SMILES: {state['smiles']}).")

        # 6. Calculate E_adsorbate
        try:
            adsorbate_only_atoms = fragment_object.conformers[0].copy()
            
            # Remove markers
            if adsorbate_only_atoms.info["smiles"] == "Cl":
                del adsorbate_only_atoms[0]
            elif adsorbate_only_atoms.info["smiles"] == "S1S":
                del adsorbate_only_atoms[:2]
                
            adsorbate_only_atoms.calc = temp_calc
            adsorbate_only_atoms.set_cell([20, 20, 20]) 
            adsorbate_only_atoms.center()
            
            logger.info(f"Relaxing isolated adsorbate for SMILES {state['smiles']}")

            # Detect single atom molecule.
            if len(adsorbate_only_atoms) > 1:
                # Protocol 1: MD Warmup (Consistent with relax_atoms)
                if md_steps > 0:
                    MaxwellBoltzmannDistribution(adsorbate_only_atoms, temperature_K=md_temp)
                    dyn_md_ads = Langevin(adsorbate_only_atoms, 1 * units.fs, temperature_K=md_temp, friction=0.01)
                    dyn_md_ads.run(md_steps)
                    
                # Protocol 2: BFGS Optimization (Consistent with relax_atoms)
                BFGS(adsorbate_only_atoms, trajectory=None, logfile=None).run(fmax=opt_fmax, steps=opt_steps)
            else:
                logger.info(
                    "Single atom adsorbate detected "
                    f"({len(adsorbate_only_atoms)} atom), skipping vacuum relaxation"
                )
            
            E_adsorbate = adsorbate_only_atoms.get_potential_energy()
            tool_logs.append(f"Success: E_adsorbate = {E_adsorbate:.4f} eV.")
            
        except Exception as e_ads_err:
            raise ValueError(f"Failed to calculate E_adsorbate: {e_ads_err}")

        # 7. Place adsorbate
        generated_traj_file = populate_surface_with_fragment(
            slab_atoms=final_slab_atoms,
            fragment_object=fragment_object,
            plan_solution=plan_solution,
            session_id=state["session_id"]
        )
        tool_logs.append(f"Success: Fragment placed on slab. Configs saved to: {generated_traj_file}")

        initial_conformers = read(generated_traj_file, index=":")
        if not initial_conformers or len(initial_conformers) == 0:
            raise ValueError(f"populate_surface_with_fragment failed to generate any configs (empty trajectory: {generated_traj_file}).")
        
        # 8. Structure Relaxation
        logger.info("Starting structure relaxation...")
        slab_indices = list(range(len(final_slab_atoms)))
        relax_n = plan_solution.get("relax_top_n", 1)
        relaxation_mode = state.get("relaxation_mode", "fast")
        logger.info(
            f"Using {backend.name} backend on device: {calc_config.device} "
            f"(relaxation_mode={relaxation_mode})"
        )

        final_traj_file = relax_atoms(
            atoms_list=list(initial_conformers),
            slab_indices=slab_indices,
            calculator=temp_calc,
            session_id=state["session_id"],
            relax_top_n=relax_n,
            fmax=opt_fmax,
            steps=opt_steps,
            md_steps=md_steps,
            md_temp=md_temp,
            relaxation_mode=relaxation_mode,
        )
        tool_logs.append(f"Success: Structure relaxation complete (Relaxed Top {relax_n}, Mode: {relaxation_mode}). Trajectory saved to '{final_traj_file}'.")
        
        # 9. Analyze Results
        logger.info("Calling Analysis Tool...")
        analysis_json_str = analyze_relaxation_results(
            relaxed_trajectory_file=final_traj_file,
            slab_atoms=final_slab_atoms,
            original_smiles=state["smiles"],
            plan_dict=plan_json,
            session_id=state["session_id"],
            e_surface_ref=E_surface,
            e_adsorbate_ref=E_adsorbate
        )
        tool_logs.append("Success: Analysis tool executed.")
        analysis_json = json.loads(analysis_json_str)
        analysis_json["generated_conformers_file"] = generated_traj_file
        analysis_json["relaxation_trajectory_file"] = final_traj_file
        analysis_json["session_id"] = state["session_id"]
        logger.info(f"Analysis Result: {json.dumps(analysis_json)}")

        if analysis_json.get("status") == "success":
            e_new = analysis_json.get("most_stable_energy_eV")
            is_dissociated = analysis_json.get("is_dissociated")

            # Logic Branch A: Molecular State
            if not is_dissociated:
                e_old_mol = new_best_molecular.get("most_stable_energy_eV", float('inf')) if new_best_molecular else float('inf')
                if isinstance(e_new, (int, float)) and e_new < e_old_mol:
                    logger.info(f"New Best Found [Molecular]: {e_new:.4f} eV")
                    new_best_molecular = {
                        "most_stable_energy_eV": e_new,
                        "analysis_json": analysis_json,
                        "plan": state.get("plan"),
                        "result_type": "Perfect" if analysis_json.get("bond_change_count")==0 else "Isomerized"
                    }

            # Logic Branch B: Dissociated State
            else:
                e_old_diss = new_best_dissociated.get("most_stable_energy_eV", float('inf')) if new_best_dissociated else float('inf')
                if isinstance(e_new, (int, float)) and e_new < e_old_diss:
                    logger.warning(f"More stable [Dissociated] state found: {e_new:.4f} eV (will serve as thermodynamic reference)")
                    new_best_dissociated = {
                        "most_stable_energy_eV": e_new,
                        "analysis_json": analysis_json,
                        "plan": state.get("plan"),
                        "result_type": "Dissociated"
                    }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Tool Execution Failed: {error_message}")
        tool_logs.append(f"Error during tool execution: {error_message}")
        analysis_json = {"status": "error", "message": f"Tool execution failed: {error_message}"}
        
    # Record attempted plan key for duplicate detection in plan_validator_node
    updated_keys = list(state.get("attempted_keys", []))
    plan_key = make_plan_key(state.get("plan"))
    if plan_key is not None and plan_key not in updated_keys:
        updated_keys.append(plan_key)

    updated_history = list(state.get("history", []))
    if isinstance(analysis_json, dict):
        try:
            updated_history.append(
                build_history_entry(
                    state.get("plan"),
                    analysis_json,
                    new_best_molecular,
                    enable_slip_feedback=state.get("enable_slip_feedback", True),
                    enable_forbid=state.get("enable_forbid", True),
                    enable_termination=state.get("enable_termination", True),
                )
            )
        except Exception as history_error:
            updated_history.append(f"History generation exception: {history_error}")

    updated_attempt_records = list(state.get("attempt_records", []))
    if isinstance(analysis_json, dict):
        site_info = analysis_json.get("site_analysis", {}) or {}
        updated_attempt_records.append(
            {
                "attempt_index": len(updated_attempt_records) + 1,
                "plan": state.get("plan"),
                "plan_key": plan_key,
                "status": analysis_json.get("status"),
                "most_stable_energy_eV": analysis_json.get("most_stable_energy_eV"),
                "bond_change_count": analysis_json.get("bond_change_count"),
                "is_dissociated": analysis_json.get("is_dissociated"),
                "is_chemical_slip": site_info.get("is_chemical_slip"),
                "planned_site_type": site_info.get("planned_site_type"),
                "actual_site_type": site_info.get("actual_site_type"),
                "best_structure_file": analysis_json.get("best_structure_file"),
                "generated_conformers_file": analysis_json.get("generated_conformers_file"),
                "relaxation_trajectory_file": analysis_json.get("relaxation_trajectory_file"),
                "message": analysis_json.get("message"),
                "history_entry": updated_history[-1] if updated_history else None,
            }
        )

    return {
        "messages": [ToolMessage(content="\n".join(tool_logs), tool_call_id="tool_executor")],
        "analysis_json": json.dumps(analysis_json),
        "history": updated_history,
        "attempt_records": updated_attempt_records,
        "best_result": new_best_molecular,
        "best_dissociated_result": new_best_dissociated,
        "attempted_keys": updated_keys,
    }

def summarizer_node(state: AgentState) -> dict:
    """ 
    Node 5: Summarizer
    Function: Generate report based on global best results, distinguishing between perfect adsorption and intramolecular rearrangement.
    """
    logger.info("Calling Summarizer Node")
    llm = get_llm(
        state["api_key"],
        backend_name=state.get("llm_backend"),
        llm_config=state.get("llm_config")
    )
    
    # 1. Extract Data Sources
    best_result = state.get("best_result")
    best_dissociated = state.get("best_dissociated_result")
    last_analysis_json_str = state.get("analysis_json", "{}")
    
    try:
        last_analysis = json.loads(last_analysis_json_str)
    except (TypeError, json.JSONDecodeError):
        last_analysis = {}

    # 2. Decision: Which data to report?
    target_data = None
    plan_used = None
    source_type = "failure"
    # Priority 1: History Best
    if best_result and isinstance(best_result, dict):
        logger.info(
            "Summarizer: Locked global best plan "
            f"(E={best_result.get('most_stable_energy_eV')} eV)"
        )
        target_data = best_result.get("analysis_json")
        plan_used = best_result.get("plan")
        source_type = "success"
    
    # Priority 2: Last attempt success
    elif last_analysis.get("status") == "success" and last_analysis.get("is_covalently_bound"):
        logger.info("Summarizer: No history best, using success result from last step")
        target_data = last_analysis
        plan_used = state.get("plan")
        source_type = "success"
    
    else:
        logger.info("Summarizer: All attempts failed")
        source_type = "failure"

    # 3. Construct Prompt
    if source_type == "success":
        data_str = json.dumps(target_data, indent=2, ensure_ascii=False)
        plan_str = json.dumps(plan_used, indent=2, ensure_ascii=False)
        
        # [New] Prepare dissociated state comparison data
        diss_warning_context = ""
        if best_dissociated:
            e_mol = target_data.get("most_stable_energy_eV", 999)
            e_diss = best_dissociated.get("most_stable_energy_eV", 999)
            if e_diss < e_mol:
                delta_E = e_diss - e_mol
                diss_warning_context = (
                    f"\n*** SEVERE THERMODYNAMIC WARNING ***\n"
                    f"Although the user requested molecular adsorption, the system found a lower energy dissociated state in history.\n"
                    f"- Molecular State Energy: {e_mol:.3f} eV\n"
                    f"- Dissociated State Energy: {e_diss:.3f} eV (More stable by {abs(delta_E):.3f} eV)\n"
                    f"This means the reported molecular state is thermodynamically metastable and prone to spontaneous dissociation."
                )

        final_prompt = f"""
        You are a rigorous computational chemist. Your task is to write a final experimental report based on the provided [OBJECTIVE FACTS].

        !!! SEVERE WARNING & SCIENTIFIC STANDARDS !!!
        1. **Precision Judgment**: Due to hardware limits, calculations use float32 precision. Energy differences < 0.05 eV may be due to **"numerical noise"** or **"energy degeneracy"**. If you find sub-optimal sites with energy differences within this range, you MUST declare in the report that they are competitive at room temperature. **DO NOT** arbitrarily claim one is the unique absolute best.
        2. **Label Correction**: Tools might incorrectly label high-coordination adsorption (Hollow) as "desorbed" based on geometric distance.
        3. **Heterogeneity Judgment**: For alloy surfaces (e.g., Ru3Mo), the same type of site (e.g., Bridge Ru-Ru) may exist in multiple environments. If history shows different results for two attempts at Bridge sites, point out in the discussion that this is due to **"surface heterogeneity"**.
        4. **No Fabrication**: Strictly base on JSON data.

        **User Request:** {state['user_request']}

        **Best Adsorption Configuration Data:**
        ```json
        {data_str}
        ```

        {diss_warning_context}

        **Initial Plan:**
        ```json
        {plan_str}
        ```

        **Writing Requirements:**
        1.  **Conclusion:** Directly answer the user request. If energy degeneracy (<0.05 eV) exists, explicitly state that multiple competitive configurations exist.
        2.  **Data Support:** List `most_stable_energy_eV` (3 decimal places) and `final_bond_distance_A`.
        3.  **Geometric Details:** Describe `bonded_surface_atoms`, and explicitly mention specific atom indices (e.g., Ru #41) to reflect site uniqueness.
        4.  **Site Correction & Slip:** Describe if a slip occurred from `planned_site_type` to `actual_site_type`.
        5.  **Chemical State Judgment:** - **Perfect Adsorption**: `bond_change_count == 0`
            - **Isomerization/Rearrangement**: `bond_change_count > 0` but not dissociated
            - **Dissociation**: `is_dissociated == True`
        """
    else:
        fail_reason = state.get("validation_error") or last_analysis.get(
            "message",
            "No stable configuration found.",
        )
        final_prompt = f"""
        You are an error reporting assistant.
        Task: Politely inform the user that after multiple attempts, no stable adsorption configuration meeting the requirements was found.
        Error Log: "{fail_reason}"
        Please suggest the user check the SMILES or change the surface model. Do not fabricate results.
        """

    # 4. Call LLM
    response = llm.invoke([HumanMessage(content=final_prompt)])
    input_tokens, output_tokens = extract_token_usage(response)
    
    logger.info("Summarizer response generated")
    payload = {
        "messages": [AIMessage(content=response.content)],
        "total_input_tokens": state.get("total_input_tokens", 0) + input_tokens,
        "total_output_tokens": state.get("total_output_tokens", 0) + output_tokens,
    }
    if should_end_after_summarizer(state):
        try:
            from adsmind.agent.reporting import write_summarizer_report

            report_artifacts = write_summarizer_report(
                state=state,
                final_text=response.content,
                target_data=target_data,
                plan_used=plan_used,
                source_type=source_type,
            )
            payload.update(report_artifacts)
            logger.info("Summarizer report written to %s", report_artifacts.get("summary_report_file"))
        except Exception as report_error:
            logger.error("Summarizer report generation failed: %s", report_error)
            payload["visualization_error"] = f"Summarizer report generation failed: {report_error}"
    return payload

# --- 4. Define Graph Logic Flow (Edges) ---
def route_after_validation(state: AgentState) -> str:
    logger.info("Python Decision Branch 1 (Validator)")
    if state.get("validation_error"):
        validation_retry_count = int(state.get("validation_retry_count", 0) or 0)
        if validation_retry_count >= get_max_attempts(state):
            logger.info(
                "Decision: Reached validation retry limit (%s). Going to Summarizer.",
                validation_retry_count,
            )
            return "summarizer"
        logger.info("Decision: Plan failed, returning to Planner ")
        return "planner"
    
    # Routing logic
    plan_json = state.get("plan", {})
    solution = plan_json.get("solution", {})
    if solution.get("action") == "terminate":
        logger.info("Decision: Planner requested termination, going to Summarizer ")
        return "summarizer"  # Skip Tool Executor, go directly to report
    
    else:
        logger.info("Decision: Plan passed, going to Tool Executor ")
    return "tool_executor"


def should_end_after_summarizer(state: AgentState) -> bool:
    """
    Return whether the summarizer should terminate the graph after this pass.
    """
    # 1. Priority Check: If previous Planner decided to terminate, and we just finished Summarizer,
    #    then we must end the process now.
    plan_solution = state.get("plan", {}).get("solution", {})
    if plan_solution.get("action") == "terminate":
        return True

    validation_retry_count = int(state.get("validation_retry_count", 0) or 0)
    if state.get("validation_error") and validation_retry_count >= get_max_attempts(state):
        return True

    try:
        analysis_data = json.loads(state.get("analysis_json", "{}"))
        if analysis_data.get("status") == "fatal_error":
            return True
    except Exception:
        pass

    current_history = state.get("history", [])
    total_attempts = len(current_history) + validation_retry_count
    return total_attempts >= get_max_attempts(state)


def route_after_analysis(state: AgentState) -> str:
    """
    Simplified Router: Generates rich history and decides next step.
    """
    logger.info("Python Decision Branch 3 (Summarizer)")

    if should_end_after_summarizer(state):
        current_history = state.get("history", [])
        validation_retry_count = int(state.get("validation_retry_count", 0) or 0)
        total_attempts = len(current_history) + validation_retry_count
        logger.info(
            "Decision: Summarizer terminal condition reached (%s tool attempts + %s validation retries = %s total). Process ending. ",
            len(current_history),
            validation_retry_count,
            total_attempts,
        )
        return "end"
    
    return "planner"

# --- 5. Build and Compile Graph ---
def get_agent_executor():
    """Build and compile the AdsMind state machine graph."""
    workflow = StateGraph(AgentState)
    workflow.add_node("pre_processor", pre_processor_node)
    workflow.add_node("planner", solution_planner_node)
    workflow.add_node("plan_validator", plan_validator_node) 
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.set_entry_point("pre_processor")
    workflow.add_edge("pre_processor", "planner")
    workflow.add_edge("planner", "plan_validator")
    workflow.add_edge("tool_executor", "summarizer")
    workflow.add_conditional_edges(
        "plan_validator",
        route_after_validation,
        {"tool_executor": "tool_executor", "planner": "planner", "summarizer": "summarizer"}
    )
    workflow.add_conditional_edges(
        "summarizer",
        route_after_analysis,
        {"planner": "planner", "end": END}
    )
    return workflow.compile()

# --- 6. Run Program ---
def _prepare_initial_state(
    smiles: str, 
    slab_path: str, 
    user_request: str,
    api_key: str,
    session_id: str,
    llm_backend: str = None,
    llm_config: dict = None,
    calculator_backend: str = None,
    calculator_config: dict = None,
    relaxation_config: dict = None,
    random_seed: int = None,
    relaxation_mode: str = "fast",
    enable_slip_feedback: bool = True,
    enable_forbid: bool = True,
    enable_termination: bool = True,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> AgentState:
    """
    Prepare initial agent state with session isolation.
    
    Args:
        smiles: SMILES string for the adsorbate
        slab_path: Path to slab structure file (supports XYZ, CIF, PDB, SDF, MOL, POSCAR)
        user_request: User's natural language request
        api_key: API key for this session (required for cloud backends)
        session_id: UUID for file path isolation
        llm_backend: LLM backend name ("openai", "anthropic", "openrouter",
            "ollama", "huggingface")
        llm_config: Optional LLM configuration overrides
        random_seed: Optional random seed for reproducible runs (None = not fixed)
        relaxation_mode: "fast" (all slab fixed) or "standard" (bottom 1/3 fixed)
    """
    return {
        "session_id": session_id,
        "api_key": api_key,
        "llm_backend": llm_backend or get_llm_backend_name(),
        "llm_config": llm_config,
        "calculator_backend": calculator_backend or get_calculator_backend(),
        "calculator_config": calculator_config,
        "relaxation_config": relaxation_config,
        "random_seed": random_seed,
        "relaxation_mode": relaxation_mode,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "enable_slip_feedback": enable_slip_feedback,
        "enable_forbid": enable_forbid,
        "enable_termination": enable_termination,
        "max_attempts": max_attempts,
        "validation_retry_count": 0,
        "smiles": smiles,
        "slab_path": slab_path,
        "surface_composition": None,
        "user_request": user_request,
        "plan": None,
        "validation_error": None,
        "messages": [HumanMessage(content=f"SMILES: {smiles}\nSLAB: {slab_path}\nREQUEST: {user_request}")],
        "analysis_json": None,
        "history": [],
        "attempt_records": [],
        "best_result": None,
        "best_dissociated_result": None,
        "attempted_keys": [],
        "available_sites_description": None,
        "summary_report_file": None,
        "best_configuration_png": None,
        "iteration_energy_curve_png": None,
        "visualization_error": None,
    }

def parse_args():
    parser = argparse.ArgumentParser(description="Run AdsMind.")
    parser.add_argument("--smiles", type=str, required=True, help="SMILES string.")
    parser.add_argument("--slab_path", type=str, required=True, help="Path to the slab structure file (XYZ, CIF, PDB, SDF, MOL, POSCAR).")
    parser.add_argument("--user_request", type=str, default="Find a stable adsorption configuration.", help="User's request.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible runs.")
    parser.add_argument("--relaxation-mode", type=str, choices=["fast", "standard"], default="fast",
                        help="Surface relaxation mode: 'fast' (all slab fixed) or 'standard' (bottom 1/3 fixed)")
    return parser.parse_args()

def main_cli():
    args = parse_args()
    if not os.path.exists('./outputs'):
        os.makedirs('./outputs')
    
    # Get LLM backend from environment or config (need this first to get correct API key)
    from adsmind.utils.config import get_llm_backend_name as get_backend_name, get_api_key_for_backend
    llm_backend = get_backend_name()
    
    # Get API key for the specific backend
    api_key, key_source = get_api_key_for_backend(llm_backend)
    if key_source:
        logger.info(f"API key loaded from {key_source} for backend: {llm_backend}")
    
    # Generate session ID for file isolation
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    # Get relaxation mode from args
    relaxation_mode = getattr(args, 'relaxation_mode', 'fast')
    
    initial_state = _prepare_initial_state(
        smiles=args.smiles, 
        slab_path=args.slab_path, 
        user_request=args.user_request,
        api_key=api_key,
        session_id=session_id,
        llm_backend=llm_backend,
        random_seed=args.seed,
        relaxation_mode=relaxation_mode
    )
    
    agent_executor = get_agent_executor()
    seed_info = f", Seed: {args.seed}" if args.seed is not None else ""
    mode_info = f", Mode: {relaxation_mode}"
    print(f"\n--- 🚀 AdsMind Started (Backend: {llm_backend}{seed_info}{mode_info}) ---\n")
    final_state = None

    config = {"recursion_limit": 50}

    for chunk in agent_executor.stream(initial_state, config=config, stream_mode="values"):
        final_state = chunk
        if "messages" in final_state and final_state["messages"]:
            last_message = final_state["messages"][-1]
            if isinstance(last_message, (AIMessage, ToolMessage)):
                print("\n---")
                print(f"[{last_message.type}]")
                print(last_message.content)
                print("---\n")
    print("\n--- 🏁 AdsMind Task Completed ---\n")
    print("Final Analysis Report:")
    if final_state and "messages" in final_state:
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                print(msg.content)
                break
        else:
             print("No final AI message found.")

if __name__ == '__main__':
    main_cli()
