import os
import re
import tempfile
import uuid
from pathlib import Path

import streamlit as st
from adsmind.agent.agent import get_agent_executor, _prepare_initial_state
from adsmind.utils.config import (
    get_llm_backend_name, get_api_key_for_backend, save_api_key_for_backend,
    save_llm_backend, is_cloud_backend, CONFIG_FILE_PATH, LLM_API_KEY_ENV_VARS
)

st.set_page_config(page_title="AdsMind", layout="wide")
st.title("AdsMind")

@st.cache_resource
def initialize_agent_executor():
    return get_agent_executor()

agent_executor = initialize_agent_executor()

def render_message(content):
    parts = re.split(r"(```python\n.*\n```)", content, flags=re.DOTALL)
    for part in parts:
        if part.strip():
            if part.startswith("```python"):
                code_to_display = part.split("\n", 1)[1].rsplit("\n```", 1)[0]
                st.code(code_to_display, language="python")
            else:
                st.markdown(part)

def render_message_in_status(content, status):
    parts = re.split(r"(```python\n.*\n```)", content, flags=re.DOTALL)
    for part in parts:
        if part.strip():
            if part.startswith("```python"):
                code_to_display = part.split("\n", 1)[1].rsplit("\n```", 1)[0]
                status.code(code_to_display, language="python")
            else:
                status.markdown(part)

# --- LLM Backend Configuration ---
st.sidebar.header("🤖 LLM Backend")

# Available backends with descriptions
LLM_BACKENDS = [
    "openai",
    "anthropic",
    "openrouter",
    "ollama",
    "huggingface",
]
LLM_BACKEND_LABELS = {
    "openai": "OpenAI (GPT)",
    "anthropic": "Anthropic (Claude)",
    "openrouter": "OpenRouter (Gemini/Grok)",
    "ollama": "Ollama (Local)",
    "huggingface": "HuggingFace (Local)",
}
LLM_BACKEND_DESCRIPTIONS = {
    "openai": "Official OpenAI endpoint for GPT models.",
    "anthropic": "Direct access to Anthropic Claude models through Anthropic's API.",
    "openrouter": "OpenRouter endpoint for Gemini and Grok models.",
    "ollama": "Run models locally. Free, private, no internet required.",
    "huggingface": "Load HuggingFace models locally. Full customization.",
}

LLM_BACKEND_KEY_HELP = {
    "openai": "OpenAI Platform",
    "anthropic": "Anthropic Console",
    "openrouter": "openrouter.ai",
}

# Default models for each backend
DEFAULT_MODELS = {
    "openai": ["gpt-5.4-2026-03-05"],
    "anthropic": ["claude-sonnet-4-6", "claude-opus-4-6"],
    "openrouter": [
        "google/gemini-2.5-pro",
        "x-ai/grok-4",
    ],
    "ollama": [],  # Will be populated dynamically
    "huggingface": ["Qwen/Qwen3-8B"],
}

# Load saved backend preference
saved_backend = get_llm_backend_name()
default_index = LLM_BACKENDS.index(saved_backend) if saved_backend in LLM_BACKENDS else 0

# Backend selection dropdown
selected_backend = st.sidebar.selectbox(
    "Backend",
    LLM_BACKENDS,
    index=default_index,
    format_func=lambda x: LLM_BACKEND_LABELS.get(x, x),
    help="Choose between hosted and local LLM backends",
)

# Show backend description
st.sidebar.caption(LLM_BACKEND_DESCRIPTIONS.get(selected_backend, ""))

# Save backend preference
if selected_backend != saved_backend:
    save_llm_backend(selected_backend)

# --- API Key Configuration (only for cloud backends) ---
api_key_input = None
selected_model = None
ollama_models = []
hf_quantize = None  # Only used for HuggingFace backend

if is_cloud_backend(selected_backend):
    st.sidebar.subheader("🔑 API Key")
    
    # Load API key for selected backend
    saved_key, key_source = get_api_key_for_backend(selected_backend)
    
    # Determine environment variable name
    env_var_name = LLM_API_KEY_ENV_VARS.get(selected_backend, "API_KEY")
    env_key_active = key_source == "env"
    
    # Show source indicator
    if key_source == "env":
        st.sidebar.success(f"🌍 Loaded from {env_var_name}")
    elif key_source == "config":
        st.sidebar.info("📁 Loaded from config file")
    else:
        st.sidebar.caption("✏️ Enter your API Key")
    
    # API key input field (disabled when from environment variable)
    api_key_input = st.sidebar.text_input(
        "API Key",
        value=saved_key or "",
        type="password",
        key=f"{selected_backend}_api_key",
        disabled=env_key_active,  # Lock input when from env var
        help=(
            "Get your key from "
            f"{LLM_BACKEND_KEY_HELP.get(selected_backend, 'the provider console')}"
        ),
    )
    
    # Save checkbox (disabled if env var is active)
    if not env_key_active:
        save_key_checkbox = st.sidebar.checkbox(
            "Save for future sessions",
            help=f"Saves to {CONFIG_FILE_PATH}"
        )
        
        # Save if checkbox is checked and key is different from saved
        if api_key_input and save_key_checkbox and api_key_input != saved_key:
            if save_api_key_for_backend(selected_backend, api_key_input):
                st.sidebar.success("✅ Saved!")
    
    # Model selection for cloud backends
    st.sidebar.subheader("📦 Model")
    model_options = DEFAULT_MODELS.get(selected_backend, [])
    if selected_backend in ("openai", "anthropic", "openrouter"):
        # Allow custom model input for hosted backends that expose model ids directly.
        use_custom_model = st.sidebar.checkbox(
            "Use custom model", key="custom_model_toggle"
        )
        if use_custom_model:
            selected_model = st.sidebar.text_input(
                "Model Name",
                value=model_options[0] if model_options else "",
                help="Enter the provider model id."
            )
        else:
            selected_model = st.sidebar.selectbox("Select Model", model_options)
    else:
        selected_model = st.sidebar.selectbox("Select Model", model_options)

else:
    st.sidebar.info(
        f"🏠 {LLM_BACKEND_LABELS[selected_backend]} - No API key required"
    )

    # Ollama-specific configuration
    if selected_backend == "ollama":
        import requests
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
        # Refresh button for Ollama models
        if st.sidebar.button("🔄 Refresh Models", key="ollama_refresh"):
            st.rerun()
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{ollama_host}/api/tags", timeout=2)
            if response.status_code == 200:
                st.sidebar.success("✅ Ollama is running")
                # Get available models
                models_data = response.json().get("models", [])
                ollama_models = [m.get("name", "unknown") for m in models_data]
                
                if ollama_models:
                    st.sidebar.subheader("📦 Model")
                    selected_model = st.sidebar.selectbox(
                        "Select Model",
                        ollama_models,
                        index=(
                            ollama_models.index("qwen3:8b")
                            if "qwen3:8b" in ollama_models
                            else 0
                        ),
                        help="Models available on your Ollama server",
                    )
                else:
                    st.sidebar.warning(
                        "No models found. Install with: `ollama pull qwen3:8b`"
                    )
                    selected_model = st.sidebar.text_input(
                        "Model Name", value="qwen3:8b"
                    )
            else:
                st.sidebar.warning("⚠️ Unexpected response from Ollama")
                selected_model = "qwen3:8b"
        except requests.exceptions.ConnectionError:
            st.sidebar.error("❌ Ollama not running")
            st.sidebar.code("ollama serve", language="bash")
            selected_model = "qwen3:8b"
        except Exception as e:
            st.sidebar.warning(f"⚠️ Cannot connect: {type(e).__name__}")
            selected_model = "qwen3:8b"
            
    elif selected_backend == "huggingface":
        st.sidebar.subheader("📦 Model")
        hf_models = DEFAULT_MODELS["huggingface"]
        use_custom_hf = st.sidebar.checkbox("Use custom model", key="custom_hf_toggle")
        if use_custom_hf:
            selected_model = st.sidebar.text_input(
                "Model Path",
                value="Qwen/Qwen3-8B",
                help="HuggingFace model ID or local path"
            )
        else:
            selected_model = st.sidebar.selectbox("Select Model", hf_models)
        
        # Quantization option
        hf_quantize = st.sidebar.selectbox(
            "Quantization",
            options=["none", "4bit", "8bit"],
            index=0,
            help="4bit/8bit reduces memory usage. Requires bitsandbytes library."
        )

# --- Advanced Settings (Collapsible) ---
with st.sidebar.expander("⚙️ Advanced Settings"):
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="0.0 = deterministic, 1.0 = creative"
    )
    
    max_tokens = st.number_input(
        "Max Tokens",
        min_value=256,
        max_value=16384,
        value=4096,
        step=256,
        help="Maximum response length"
    )
    
    st.markdown("---")
    st.subheader("🔬 Calculation Settings")
    
    relaxation_mode = st.selectbox(
        "Surface Relaxation Mode",
        options=["fast", "standard"],
        index=0,
        help="FAST: All surface atoms fixed (faster, for laptops). STANDARD: Bottom 1/3 fixed (more accurate, for workstations)."
    )
    
    random_seed_input = st.number_input(
        "Random Seed",
        min_value=0,
        max_value=999999,
        value=0,
        step=1,
        help="Set to 0 for random behavior, or any other value for reproducible runs"
    )
    # Convert 0 to None (meaning random)
    random_seed = None if random_seed_input == 0 else random_seed_input
    
    st.caption("These settings affect calculation behavior.")

# Build llm_config from UI settings
llm_config = {
    "model": selected_model,
    "temperature": temperature,
    "max_tokens": max_tokens,
}
# Add HuggingFace-specific options
if hf_quantize and hf_quantize != "none":
    llm_config["quantize"] = hf_quantize
# Clean up None values
llm_config = {k: v for k, v in llm_config.items() if v is not None}


st.sidebar.header("Inputs")
smiles_input = st.sidebar.text_input("Adsorbate SMILES")

# Supported structure formats (ASE-compatible)
SUPPORTED_STRUCTURE_FORMATS = ['xyz', 'cif', 'pdb', 'sdf', 'mol', 'poscar', 'vasp']
structure_file = st.sidebar.file_uploader(
    "Slab Structure File", 
    type=SUPPORTED_STRUCTURE_FORMATS,
    help="Supports XYZ, CIF, PDB, SDF, MOL, POSCAR/VASP formats"
)
user_query = st.sidebar.text_area("User Query", value="")

# Determine if Run button should be enabled
missing_requirements = []
if is_cloud_backend(selected_backend) and not api_key_input:
    missing_requirements.append("API Key")
if not smiles_input:
    missing_requirements.append("SMILES")
if not structure_file:
    missing_requirements.append("Slab Structure File")

can_run = len(missing_requirements) == 0

# Action buttons
st.sidebar.markdown("---")
col1, col2 = st.sidebar.columns(2)
with col1:
    run_button = st.button("▶️ Run", use_container_width=True, type="primary", disabled=not can_run)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

# Show missing requirements hint
if not can_run:
    st.sidebar.caption(f"⚠️ Missing: {', '.join(missing_requirements)}")

# Handle clear button - reset all session state for a fresh run
if clear_button:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_message(message["content"])

if run_button:
    # Preserve original file extension for ASE format auto-detection
    file_ext = Path(structure_file.name).suffix.lower() or ".xyz"
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='w') as tmp_file:
        file_content = structure_file.getvalue().decode('utf-8')
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name
    
    try:
        # Generate unique session ID for file isolation
        session_id = str(uuid.uuid4())[:8]  # First 8 chars for brevity
        
        # Display model being used
        model_display = llm_config.get("model", "default")
        
        initial_state = _prepare_initial_state(
            smiles=smiles_input, 
            slab_path=tmp_file_path, 
            user_request=user_query,
            api_key=api_key_input,  # May be None for local backends
            session_id=session_id,
            llm_backend=selected_backend,
            llm_config=llm_config,
            random_seed=random_seed,
            relaxation_mode=relaxation_mode
        )
        
        # User message with full configuration
        seed_display = random_seed if random_seed else "random"
        config_summary = f"**Inputs:**\n- SMILES: `{smiles_input}`\n- Structure: `{structure_file.name}`\n- Query: `{user_query}`\n\n**Config:**\n- Backend: `{LLM_BACKEND_LABELS[selected_backend]}`\n- Model: `{model_display}`\n- Relaxation: `{relaxation_mode}`\n- Seed: `{seed_display}`"
        st.session_state.messages.append({"role": "user", "content": config_summary})
        with st.chat_message("user"):
            st.markdown(config_summary)

        with st.chat_message("assistant"):
            final_answer = ""
            with st.status(f"🤖 {LLM_BACKEND_LABELS[selected_backend]} | Model: {model_display}", expanded=True) as status:
                # Show initial loading message (visible while pre-processing runs)
                status.markdown("⏳ **Initializing...** Analyzing surface structure and preparing agent...")
                
                MAX_STEPS = int(os.environ.get("AGENT_MAX_STEPS", "20"))
                step_count = 0
                recent_messages = []
                recent_tool_messages = []

                for event in agent_executor.stream(
                    initial_state,
                    stream_mode="values",
                ):
                    step_count += 1
                    if step_count >= MAX_STEPS:
                        status.markdown("⚠️ **WARNING: Reached maximum step limit. Terminating to prevent infinite loop.**")
                        break
                    if "messages" in event:
                        last_message = event["messages"][-1]
                        if last_message.content:
                            content = last_message.content
                            if last_message.type == "tool":
                                if content in recent_tool_messages:
                                    status.markdown("⚠️ **WARNING: Detected repeated tool output.**")
                                recent_tool_messages.append(content)
                                if len(recent_tool_messages) > 5:
                                    recent_tool_messages.pop(0)
                                render_message_in_status(content, status)
                                status.divider()
                            elif last_message.type == "ai":
                                if content in recent_messages:
                                    status.markdown("⚠️ **WARNING: Detected repeated message content.**")
                                recent_messages.append(content)
                                if len(recent_messages) > 5:
                                    recent_messages.pop(0)
                                render_message_in_status(content, status)
                                status.divider()
                                final_answer = content
                
                status.update(label="Agent finished.", state="complete", expanded=False)

            if final_answer:
                render_message(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            else:
                st.warning("The agent did not produce a final answer.")
        
        os.remove(tmp_file_path)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.exception(e)
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Quick Start Guide"):
    st.markdown("""
    **1. Select LLM Backend**
    - API key: OpenAI, Anthropic, or OpenRouter
    - Local: Ollama or HuggingFace
    
    **2. Enter Inputs**
    - SMILES: Molecule/ReactiveSpecies (e.g., `CO` for `CH3OH`, `O` for `H2O`)
    - Slab File: Crystal surface structure
    - Query: What you want to calculate
    
    **3. Run Agent**
    - Click ▶️ Run to start
    - Click 🗑️ Clear to reset
    """)

# Scientific disclaimer
st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ **Disclaimer**: AdsMind is an AI-assisted screening tool. "
    "Results should be validated with DFT or experimental methods before publication. "
    "Energy values are computed at 0K without thermal/entropic corrections. "
    "See [documentation](https://github.com/AI4QC/AdsMind/blob/main/docs/quickstart.md) for details."
)
