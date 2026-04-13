# Phase 7 Audit: Claude Sonnet 4.6 + EPFL Control

Date: 2026-04-14
Source branch: `origin/claude`
Source commit: `53f1eb1 data: add claude sonnet 4.6 and epfl control results`

## Executive Summary

The Claude Sonnet 4.6 result package is usable, but the branch must not be merged wholesale.

- Claude one-shot completed with `18/20` valid adsorption structures.
- Failed one-shot cases are `06` and `08`; both are NNH dissociation outcomes, not API/runtime failures.
- Claude ablation completed `25/25` runs successfully.
- EPFL cross-machine control confirms that the current Mac-vs-EPFL comparison is not a pure LLM-backend comparison: case `14` shifts by about `0.19-0.21 eV` on both Gemini and Grok-4 while preserving the same one-shot search trajectory class.
- The branch also reverts the repo-root path resolution fix in `research/agent_eval`; those code changes are a regression and should not be merged into `main`.

## Data Integrity Checks

Checks performed against the branch contents:

- Parsed `49` tracked `result.json` files successfully:
  - `20` Claude one-shot case results
  - `25` Claude ablation case results
  - `4` EPFL control case results
- No plaintext API key material was found in the staged result/report/config payload.
- Claude one-shot summary row count: `20`
- Claude ablation summary row count: `25`
- EPFL control summary row counts:
  - Gemini: `2`
  - Grok-4: `2`

## Claude Sonnet 4.6 Results

### One-shot

- Total cases: `20`
- Successful valid adsorption results: `18`
- Failed cases: `06`, `08`
- Failure mode for both failed cases: one-shot NNH dissociation (`dissociation_count = 1`)
- Mean tokens per case: `6385.25`
- Successful cases with at least one chemical slip: `12`

Interpretation:

- Claude raw one-shot quality is in the same qualitative regime as the OpenAI GPT-5.4 run: the backend is usable, but NNH systems `06/08` are persistent failure cases under the single-shot protocol.
- The failed dissociated energies must not be reported as valid adsorption energies.

### Ablation

- Total runs: `25`
- Successful runs: `25`
- Friedman test: `p = 0.00984`
- Mean full-vs-single-shot improvement (`single_shot - full`): `0.16258 eV`

Per-case full vs single-shot deltas:

- `01`: `+0.07288 eV`
- `02`: `+0.42618 eV`
- `09`: `+0.18752 eV`
- `14`: `+0.12631 eV`
- `19`: `+0.00000 eV`

Variant-specific observations:

- `no_slip` improves case `19` by `-0.13628 eV`
- `no_forbid` improves case `19` by `-0.13628 eV`
- `no_termination` is nearly neutral overall (mean delta `-0.00230 eV`)

Interpretation:

- Claude supports the same broad agentic claim as Gemini, Grok-4, and GPT-5.4: the closed-loop `full` variant improves on the one-shot baseline on average.
- Like GPT-5.4, Claude also shows that slip/FORBID are not uniformly monotonic; for case `19`, removing them can improve the final energy. This is a real negative-control result and should be reported transparently rather than forced into a one-direction narrative.

## EPFL Cross-Machine Control

The control compared Mac one-shot baselines with EPFL workstation one-shot reruns for Gemini and Grok-4 on cases `09` and `14`.

Observed energy deltas (`EPFL - Mac`):

- Gemini `09`: `-0.00235 eV`
- Gemini `14`: `-0.20822 eV`
- Grok-4 `09`: `-0.00332 eV`
- Grok-4 `14`: `-0.18529 eV`

Case `14` detail:

- Gemini and Grok-4 both preserve:
  - `status = success`
  - `iteration_count = 1`
  - `final_site_type = bridge`
  - `chemical_slip_count = 1`
  - `dissociation_count = 0`
  - `rearrangement_count = 0`

Interpretation:

- Case `09` is numerically stable across machines.
- Case `14` is not.
- Because Gemini and Grok-4 both drift on `14` while preserving the same one-shot search pattern, this is best interpreted as a platform/environment effect, not an LLM decision-path effect.
- Therefore the current dataset supports:
  - same-platform comparisons: valid
  - cross-platform four-backend absolute ranking: not yet clean enough

## Code Review Finding

The branch includes unrelated code changes in:

- `research/agent_eval/common.py`
- `research/agent_eval/run_case.py`
- `research/agent_eval/run_batch.py`
- `research/agent_eval/run_ablation.py`
- `research/agent_eval/summarize_runs.py`
- `tests/test_agent_eval_tools.py`

These changes remove repo-root-aware path resolution and delete the corresponding tests.

Concrete regression reproduced during audit:

- Current `main`: running `python -m research.agent_eval.run_batch ...` from a nested working directory succeeds because repo-root-relative manifest/config paths are resolved correctly.
- `origin/claude`: the same invocation fails with `FileNotFoundError: research/agent_eval/manifests/cmu_manifest.csv`.

Recommendation:

- import the result files from `origin/claude`
- do **not** merge the runner/tooling code changes from that branch

## Merge Recommendation

Safe to merge into `main`:

- Claude one-shot result package:
  - `research/results/cmu_v1_anthropic_sonnet46_one_shot/`
- Claude ablation result package:
  - `research/results/anthropic_sonnet46_ablation_v1/`
- EPFL control result packages:
  - `research/results/cmu_v1_gemini_one_shot_epfl_control/`
  - `research/results/cmu_v1_xai_progressive_one_shot_epfl_control/`

Do not merge into `main`:

- the runner/tooling code diffs from `origin/claude`
- any paper-facing claim that treats Mac and EPFL runs as a single platform-controlled four-backend benchmark

## Next Step Recommendation

For a clean four-backend same-platform comparison, run the minimal EPFL alignment set:

- Gemini EPFL ablation subset: cases `01,02,09,14,19`, variants `full,single_shot`
- Grok-4 EPFL ablation subset: cases `01,02,09,14,19`, variants `full,single_shot`

That `20`-run supplement is enough to move the key agentic-gain comparison onto a single platform without rerunning the entire historical benchmark.
