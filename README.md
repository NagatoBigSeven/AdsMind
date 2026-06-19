# AdsMind

[![CI](https://github.com/NagatoBigSeven/AdsMind/actions/workflows/ci.yml/badge.svg)](https://github.com/NagatoBigSeven/AdsMind/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AdsMind is the codebase for the manuscript "AdsMind: A Physics-Grounded
Multi-Agent System for Self-Correcting Discovery of Adsorption Configurations on
Heterogeneous Catalyst Surfaces." AdsMind stands for "Adsorption configuration
discovery with Machine intelligence and relaxation feedback": a closed-loop
multi-agent framework that uses machine-learning force-field relaxation feedback
to help an LLM planner detect, diagnose, and recover from erroneous adsorption
configuration proposals.

The public repository contains the Python package, a Streamlit UI, curated
benchmark inputs, and reproducibility scripts/results used for AdsMind research
experiments.

## Highlights

- Multi-backend LLM interface: OpenRouter, OpenAI, Anthropic, Ollama, and local
  HuggingFace models.
- ASE-compatible calculator abstraction with MACE-MP as the default backend.
- Closed-loop planning, validation, execution, and summarization for
  self-correcting adsorption-configuration search.
- CLI and Streamlit entry points for scripted and interactive use.
- Curated manuscript benchmark inputs under `datasets/`: `cmu20/` stores the
  20-case AA20 benchmark, `ocd62/` stores OCD-GMAE62, and
  `ocd62_overlap12/` stores the 12-case reproducibility subset.
- Research scripts and paper-facing result summaries under `research/`.

## Installation

AdsMind currently supports Python 3.10 and 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run a lightweight environment check:

```bash
adsmind-preflight --json
```

For hosted LLMs, configure a backend and API key:

```bash
cp .env.example .env
export ADSMIND_LLM_BACKEND=openrouter
export OPENROUTER_API_KEY=your-key-here
```

Local backends do not require hosted API keys. For example:

```bash
export ADSMIND_LLM_BACKEND=ollama
ollama pull qwen3:8b
```

## Quick Start

Run the CLI on a bundled sample slab:

```bash
adsmind \
  --smiles O \
  --slab_path datasets/samples/cu_slab_211.xyz \
  --user_request "Find a stable oxygen adsorption configuration."
```

Launch the Streamlit UI:

```bash
adsmind-ui
```

Run outputs are written under `outputs/<session-id>/`, including a Markdown
summary report and generated structure visualizations when rendering succeeds.

See [docs/quickstart.md](docs/quickstart.md) for backend configuration,
troubleshooting, and expected outputs.

## Repository Layout

```text
adsmind/          Python package: agent graph, tools, LLMs, calculators, UI
datasets/         Curated benchmark and sample structures
research/         Reproducible experiment runners, analyses, figures, results
tests/            Unit and smoke tests
assets/           Project logo and concept image
refs.bib          Standalone BibTeX references extracted from the manuscript
```

## Reproducibility

The committed datasets are small curated snapshots, so basic examples and tests
do not require redownloading benchmark structures. Paper-facing experiment
outputs live under `research/results/`; start with
[research/results/README.md](research/results/README.md) before using those
CSV/JSON/TEX files.

Large raw run payloads (trajectories, per-run artifacts, agent/driver logs) will
be distributed as a GitHub release archive (not yet published; available from
the sole first author on request in the meantime) rather than committed
directly, so a clone stays small. The committed result tree keeps only path-sanitized summaries
and per-case records. See
[paper-artifacts/MANIFEST.md](paper-artifacts/MANIFEST.md) for the artifact
archive layout.

## Citation

If you use AdsMind, cite the manuscript/software metadata in
[CITATION.cff](CITATION.cff). A BibTeX entry transcribed from the manuscript
title page is also provided in [docs/references.md](docs/references.md), and the
manuscript reference library is available as [refs.bib](refs.bib).

```bibtex
@misc{zhang2026adsmindphysicsgroundedmultiagentselfcorrecting,
      title={AdsMind: A Physics-Grounded Multi-Agent System for Self-Correcting Discovery of Adsorption Configurations on Heterogeneous Catalyst Surfaces},
      author={Zongmin Zhang and Yuyang Lou and Bowen Zhang and Junwu Chen and Ryo Kuroki and Xuan Vu Nguyen and Edvin Fako and Lixue Cheng and Philippe Schwaller},
      year={2026},
      eprint={2606.19152},
      archivePrefix={arXiv},
      primaryClass={cond-mat.mtrl-sci},
      url={https://arxiv.org/abs/2606.19152},
}
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before
opening a pull request, and use the issue templates in `.github/ISSUE_TEMPLATE/`
for bug reports or feature proposals.

## Scientific Caveat

AdsMind is an AI-assisted screening and hypothesis-generation tool. Reported
energies and configurations should be validated with higher-fidelity simulation
protocols or experiments before being used for publication-quality scientific
claims.

## License

AdsMind is released under the [MIT License](LICENSE).
