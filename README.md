<p style="text-align: center;">
  <img src="https://raw.githubusercontent.com/AI4QC/AdsMind/main/assets/adsmind_concept.png" alt="Project logo" width="80%"/>
</p>

<br>

<h1 align="left">
  AdsMind: A Physics-Grounded Multi-agent System for Self-Correcting Discovery of Adsorption Configurations on Heterogeneous Catalyst Surfaces
</h1>

<br>

Welcome to the AdsMind repository. AdsMind is an agentic framework that couples an LLM planner with a physics-grounded tool layer (MACE-MP-0 relaxations, chemical-slip diagnostics, FORBID constraints) to autonomously explore adsorbate-surface binding configurations in a closed loop.

The application, UI, and Python distribution are all named **AdsMind**.

The goal of AdsMind is to showcase how Large Language Models (LLMs) can autonomously explore the binding configurations of adsorbates on hetero-catalytic surfaces. Starting from only a SMILES string and a surface structure, the agent can:

* generate binding configurations,
* run structure relaxations,
* analyze the results, and
* iterate until a stable configuration is found.

Users can also interact with the agent - asking questions about the system or guiding the search process through prompts.

At the core of AdsMind is [AutoAdsorbate](https://github.com/basf/autoadsorbate) - a powerful tool for generating chemically meaningful molecular and fragment configurations on surfaces, providing a search space for the agent.

## ✨ Features

* **Multi-Backend LLM Support**: Google AI (Gemini), Vertex AI, Anthropic Claude, xAI Grok, OpenRouter, Ollama, HuggingFace
* **Multiple Structure Formats**: XYZ, CIF, PDB, SDF, MOL, POSCAR/VASP
* **Interactive UI**: Streamlit-based interface with real-time agent feedback
* **Local & Cloud Options**: Use cloud APIs or run completely offline with Ollama/HuggingFace

## 🚀 Quickstart

```bash
# Install from PyPI
python -m pip install adsmind

# Set API key (Google AI is default)
export GOOGLE_API_KEY="your-google-api-key"

# Run the packaged app
adsmind-ui
```

For a source checkout with the paper scripts and benchmark assets:

```bash
git clone https://github.com/AI4QC/AdsMind.git
cd AdsMind
uv pip install -e ".[dev,research]"
adsmind-ui
```

Then provide your inputs in the sidebar:

1. **SMILES**: Molecule structure (e.g., `O=C=O` for CO₂, `O` for oxygen atom)
2. **Slab File**: Upload your surface structure
3. **Query**: What you want to find
4. Click **▶️ Run**

The repository entry point `streamlit run streamlit_app.py` is also kept for
contributors working directly from a clone.

📖 See the [Quickstart Guide](https://github.com/AI4QC/AdsMind/blob/main/docs/quickstart.md) for detailed instructions.

## Repository Scope

This public repository is the medium-weight release of AdsMind: it keeps the
runtime package, documentation, small examples, manuscript source, reproduction
scripts, and curated paper-facing CSV/JSON/TEX summaries. Raw per-run payloads,
full logs, trajectories, and bulky generated structures belong in the external
artifact bundle described in the
[paper artifact manifest](https://github.com/AI4QC/AdsMind/blob/main/paper-artifacts/MANIFEST.md).

The square [assets/logo.png](https://github.com/AI4QC/AdsMind/blob/main/assets/logo.png)
is intended for the GitHub social preview and project logo. The rendered paper
pipeline and concept figures live in `assets/`.

## 🤖 LLM Backend Options

| Backend | Type | API Key | Best For |
|---------|------|---------|----------|
| **Google AI** | Cloud | `GOOGLE_API_KEY` | Production (default) |
| **Vertex AI** | Cloud | Google ADC | Enterprise Gemini deployments |
| **Anthropic** | Cloud | `ANTHROPIC_API_KEY` | Claude models |
| **xAI** | Cloud | `XAI_API_KEY` | Grok models |
| **OpenRouter** | Cloud | `OPENROUTER_API_KEY` | Multi-model access |
| **Ollama** | Local | Not needed | Privacy, offline |
| **HuggingFace** | Local | Not needed | Customization |

Select your backend in the app sidebar or via environment variable:

```bash
export ADSMIND_LLM_BACKEND=google    # or google_vertexai, anthropic, xai, openrouter, ollama, huggingface
```

Legacy `ADSKRK_LLM_BACKEND` is still accepted as a fallback.

📖 See [LLM Backends](https://github.com/AI4QC/AdsMind/blob/main/docs/llm_backends.md) for configuration details.

## 📁 Supported File Formats

| Format | Extensions |
|--------|------------|
| XYZ | `.xyz` |
| CIF | `.cif` |
| PDB | `.pdb` |
| SDF/MOL | `.sdf`, `.mol` |
| POSCAR | `.poscar`, `.vasp` |

## ⚙️ Configuration

### API Keys

Multiple ways to provide your API key (in priority order):

1. **Environment variable**:

   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   # or ANTHROPIC_API_KEY / XAI_API_KEY / OPENROUTER_API_KEY, depending on backend
   ```

2. **Config file**: Use the app's "Save for future sessions" checkbox
   * Stored at: `~/.adsmind/config.json`
   * Legacy fallback: `~/.adskrk/config.json`

3. **Manual input**: Enter in the sidebar each session

### Advanced Settings

The app provides advanced settings (click ⚙️ Advanced Settings):

* **Temperature**: 0.0 (deterministic) to 1.0 (creative)
* **Max Tokens**: 256 to 16384

## 🔬 Example: CO₂ on Copper

One particularly interesting finding was the agent's ability to reason about relaxation trajectories. For CO₂ on a copper surface, Gemini 2.5 Pro can analyze:

```text
The stability of the initial adsorption configuration was assessed by 
performing a structural relaxation. Based on the output from the simulation, 
the fragment did not remain bound to the surface.
...
Therefore, to answer the user's question: no, the fragment does not stay 
covalently bound. The initial configuration, with the carbon atom placed 
on a top site of the Cu(211) surface, is unstable and leads to desorption.
```

## 📚 Documentation

* [Quickstart Guide](https://github.com/AI4QC/AdsMind/blob/main/docs/quickstart.md) - Get started in 5 minutes
* [LLM Backends](https://github.com/AI4QC/AdsMind/blob/main/docs/llm_backends.md) - Configure LLM providers
* [Calculator Backends](https://github.com/AI4QC/AdsMind/blob/main/docs/calculator_backends.md) - MACE and other calculators
* [Architecture](https://github.com/AI4QC/AdsMind/blob/main/docs/architecture.md) - Runtime components and data flow
* [Support Matrix](https://github.com/AI4QC/AdsMind/blob/main/docs/support_matrix.md) - Supported environments and backend maturity
* [Runtime Operations](https://github.com/AI4QC/AdsMind/blob/main/docs/runtime_operations.md) - Outputs, session isolation, and runtime controls

## 👩‍💻 Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run preflight checks
adsmind-preflight --ci

# Compile source and research entrypoints
python -m compileall adsmind tests streamlit_app.py research

# Run tests
python -m unittest discover -s tests -p 'test_*.py' -v
```

## 📦 Release Checks

Before publishing a GitHub release or uploading to PyPI, build from a clean
public snapshot and run:

```bash
python -m build --sdist --wheel
twine check dist/*
python -m unittest discover -s tests -p 'test_*.py' -v
```

See [RELEASE.md](https://github.com/AI4QC/AdsMind/blob/main/RELEASE.md) for the full pre-release checklist.

## 📖 Citation

If you use AdsMind, please cite:

```text
AdsMind: A Physics-Grounded Multi-agent System for Self-Correcting Discovery
of Adsorption Configurations on Heterogeneous Catalyst Surfaces.
```

Structured citation metadata is available in [CITATION.cff](https://github.com/AI4QC/AdsMind/blob/main/CITATION.cff).

## 📄 License

MIT License - see [LICENSE](https://github.com/AI4QC/AdsMind/blob/main/LICENSE) file.

## 🙏 Acknowledgments

* [AutoAdsorbate](https://github.com/basf/autoadsorbate) - Surface configuration generation
* [MACE](https://github.com/ACEsuit/mace) - Machine learning interatomic potentials
* [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
