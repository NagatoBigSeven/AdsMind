# Architecture

AdsMind is the application name used in the UI, documentation, and packaging.

## Runtime Flow

1. `adsmind-ui` launches the packaged Streamlit UI from `adsmind.app.app`.
2. The UI collects the adsorbate SMILES, slab file, backend selection, and
   runtime settings, then prepares the initial graph state.
3. `adsmind.agent.agent` runs a LangGraph workflow:
   - `pre_processor`: scans the slab and available adsorption sites
   - `planner`: asks the selected LLM for the next adsorption plan
   - `plan_validator`: enforces JSON shape and chemistry constraints
   - `tool_executor`: runs slab preparation, fragment placement, relaxation,
     and result analysis
   - `summarizer`: turns the best available result into a Markdown report with
     deterministic visualizations
4. `adsmind.tools.tools` handles the chemistry and simulation logic:
   - AutoAdsorbate monkey patches
   - slab cleanup and expansion
   - fragment construction and site population
   - MACE-backed relaxation
   - adsorption energy and bonding analysis

## Backends

- LLM backends live in `adsmind/llms/`
- calculator backends live in `adsmind/calculators/`
- configuration and logging live in `adsmind/utils/`

## Outputs

- Session outputs are written under `outputs/<session_id>/`
- API keys and the preferred LLM backend are stored in `~/.adsmind/config.json`
- The legacy `~/.adskrk/config.json` path is still read as a fallback.
- See `docs/runtime_operations.md` for output lifecycle, session isolation, and runtime controls.

## Compatibility

- See `docs/support_matrix.md` for supported Python versions, operating systems, and backend maturity levels.

## Research Assets

Research-only scripts and paper assets are kept separate from the runtime code.
See `research/README.md` for figure generation and `overleaf/` for the
manuscript source.
