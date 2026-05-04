# Quickstart Guide

Get AdsMind running in 5 minutes.

## Prerequisites

- Python 3.10 or 3.11
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- API key from OpenRouter, OpenAI, or Anthropic for hosted API backends

## Installation

### PyPI Install

```bash
python -m pip install adsmind
```

### Source Install

Use this path if you want the repository examples, benchmark assets, tests, or
paper reproduction scripts.

```bash
git clone https://github.com/AI4QC/AdsMind.git
cd AdsMind
uv pip install -e ".[dev,research]"
```

## Step 1: Set Up LLM Backend

### Option A: OpenRouter

Use this route for Gemini and Grok.

```bash
export ADSMIND_LLM_BACKEND=openrouter
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

### Option B: OpenAI

Use this route for GPT.

```bash
export ADSMIND_LLM_BACKEND=openai
export OPENAI_API_KEY="your-openai-api-key"
```

### Option C: Anthropic

Use this route for Claude.

```bash
export ADSMIND_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Option D: Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:8b
ollama serve
```

## Step 2: Launch the App

```bash
adsmind-ui
```

The app will open in your browser at `http://localhost:8501`.

When working from a source checkout, `streamlit run streamlit_app.py` remains
available as an equivalent contributor entry point.

## Step 3: Run Your First Simulation

### 1. Select LLM Backend

- Choose OpenRouter, OpenAI, Anthropic, Ollama, or HuggingFace.
- Enter an API key if using a hosted backend.
- Select a model.

### 2. Enter Inputs

| Input | Description | Example |
|-------|-------------|---------|
| **SMILES** | Molecule/ReactiveSpecies | `O=C=O`, `O`, `CO` |
| **Slab File** | Surface structure file | Upload XYZ, CIF, or POSCAR |
| **Query** | What you want to find | "Find the most stable adsorption site" |

### 3. Click "Run"

The agent will parse the adsorbate and slab, propose adsorption configurations,
run MACE relaxations, analyze the results, and iterate until it reports the best
configuration found.

## Supported File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| XYZ | `.xyz` | Standard XYZ coordinates |
| CIF | `.cif` | Crystallographic Information File |
| PDB | `.pdb` | Protein Data Bank format |
| SDF/MOL | `.sdf`, `.mol` | MDL Molfile format |
| POSCAR | `.poscar`, `.vasp` | VASP structure format |
