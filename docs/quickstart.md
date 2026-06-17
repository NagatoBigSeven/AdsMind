# Quickstart

This guide gets AdsMind running from a fresh checkout. It assumes Python 3.10 or
3.11 and a shell with access to the repository root.

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Verify that the package imports, the agent graph compiles, and configured
backends are discoverable:

```bash
adsmind-preflight --json
```

## Configure an LLM Backend

Hosted backend example:

```bash
export ADSMIND_LLM_BACKEND=openrouter
export OPENROUTER_API_KEY=your-key-here
```

Other hosted options:

```bash
export ADSMIND_LLM_BACKEND=openai
export OPENAI_API_KEY=your-key-here
```

```bash
export ADSMIND_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY=your-key-here
```

Local Ollama example:

```bash
export ADSMIND_LLM_BACKEND=ollama
ollama pull qwen3:8b
```

Local HuggingFace example:

```bash
export ADSMIND_LLM_BACKEND=huggingface
export HF_MODEL=Qwen/Qwen3-8B
```

## Run the CLI

```bash
adsmind \
  --smiles O \
  --slab_path datasets/samples/cu_slab_211.xyz \
  --user_request "Find a stable oxygen adsorption configuration."
```

Useful options:

```bash
adsmind \
  --smiles CO \
  --slab_path datasets/samples/CuZnO.xyz \
  --user_request "Find a stable CO adsorption configuration." \
  --seed 7 \
  --relaxation-mode fast
```

`fast` keeps all slab atoms fixed and is better for laptops. `standard` relaxes
the upper part of the slab and is better suited to workstations.

## Run the UI

```bash
adsmind-ui
```

The UI lets you choose an LLM backend, enter or reuse an API key, upload a slab
structure, set the adsorbate SMILES, and run the agent interactively.

## Outputs

Each run writes to `outputs/<session-id>/`. Typical artifacts include:

- `summary_report.md`: per-round reasoning, validation, and final narrative,
- `best_configuration.png`: rendered best structure, when rendering succeeds,
- generated `.xyz`/`.traj` files used during relaxation.

Runtime outputs are ignored by Git. Promote only curated, documented artifacts
into release archives.

## Common Issues

- Missing API key: set the key for the selected hosted backend, or switch to a
  local backend.
- MACE initialization is slow on the first run: the model may need to download
  and load into memory.
- Apple Silicon precision: AdsMind uses MACE CPU float32 defaults on macOS to
  avoid unsupported FP64 paths.
- Unsupported structure file: the CLI and UI rely on ASE readers. Try XYZ, CIF,
  PDB, SDF, MOL, POSCAR, or VASP formats.

