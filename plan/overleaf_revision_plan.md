# Overleaf Manuscript Revision Plan

## Status as of 2026-04-27

This is a **current-stage manuscript plan**, not the final rewrite plan. The paper should not be fully rewritten around final ablation conclusions until all remote experiment batches are complete and the post-processing summaries have been rebuilt.

Current known incompleteness:

- Some large ablation/recovery batches on the remote workstation are still running or require final pull/rebuild.
- Grok/Gemini recovery status has changed several times because of external API quota/routing failures; external failures must stay out of formal chemistry statistics until reruns are complete.
- DFT validation is currently only a case 01 MVP package, not a completed DFT alignment result.
- Bowen's DFT final structures/settings are not yet available locally.
- Lou/PI are still actively shaping figures and some manuscript language.

Therefore, the immediate manuscript work should be limited to stable, non-data-fragile edits:

- terminology cleanup (`Analyzer` / `Summarizer`);
- MACE-MP-0 protocol specificity;
- citation anchors;
- N/A/failure taxonomy language;
- data-availability/reproducibility wording that does not overclaim;
- keeping result claims clearly marked as current/locked where needed.

Current safe patch status: terminology cleanup, MACE-MP-0 specificity, MACE-MP foundation citation, and N/A/NULL caption clarifications have been applied to the Overleaf tree. Broader numerical rewrites remain deferred until the final remote experiment pull and rebuild.

After final experiment data are pulled and verified, rerun the statistical summaries and then update Introduction/Results/Discussion/SI in one coherent pass.

## Goal

Revise the Overleaf manuscript so that terminology, citations, MACE protocol, failure definitions, and ablation interpretation are internally consistent and defensible. The revision should support PI takeover and Lou Yuyang's figure/table work without overwriting their placeholders or unrelated edits.

## Constraints

- Do not fill the abstract unless explicitly asked by PI/Lou.
- Do not delete placeholders.
- Do not delete extra references.
- Do not make broad Method rewrites unless needed for technical correctness.
- Do not modify unrelated sections while Lou or PI is actively editing them.
- Do not mix external service failures into formal chemistry statistics.
- Do not report unfinished experiment batches as completed results.
- Do not promote provisional DFT trajectory labels to manuscript conclusions before DFT/PBE final structures are aligned.
- Do not rewrite result numbers from partially complete remote batches.

## Terminology Plan

### Module names

Use the following manuscript terminology:

- `Planner`
- `Validator`
- `Executor`
- `Analyzer`
- `Summarizer`

The technically precise framing is:

- The core closed-loop execution modules are `Planner`, `Validator`, `Executor`, and `Analyzer`.
- The `Summarizer` is the report-and-routing node after physical execution or explicit termination.

This avoids changing the system into a misleading five-core-module architecture while still satisfying the PI's request to rename the ambiguous final analyzer.

### Analyzer

`Analyzer` should refer only to deterministic post-relaxation structure analysis:

- reconstructing local coordination
- detecting chemical slip
- detecting canonical site mismatch
- detecting dissociation/rearrangement
- checking valid relaxed configuration status
- updating running best energy/configuration
- writing feedback artifacts to history

Avoid the phrase `post-relaxation Analyzer` as a module name. If needed, introduce once as:

```latex
the \textbf{Analyzer}, which performs post-relaxation structure analysis
```

### Summarizer

`Summarizer` should refer to the report-and-routing node:

- route back to Planner when search continues
- generate final report when terminate action is emitted
- generate final report when budget is exhausted
- summarize the best configuration and trajectory

Recommended first-use sentence:

```latex
The report-and-routing node, referred to here as the \textbf{Summarizer}, corresponds to the code-level final analyzer node.
```

Do not continue using `Final Analyzer` in the manuscript.

## MACE Protocol Plan

### Primary protocol

All primary benchmark and matched-baseline experiments should be described as:

```latex
MACE-MP-0 small, CPU, float32, dispersion disabled
```

This is supported by the frozen configs:

- `mace_model = small`
- `mace_device = cpu`
- `mace_precision = float32`
- `mace_use_dispersion = false`

### Sensitivity protocol

The sensitivity experiments should be described as:

```latex
MACE-MP-0 large, CUDA/GPU, float64, dispersion enabled
```

This is supported by `frozen_config_openai_gpt54_mace_large.json`:

- `mace_model = large`
- `mace_device = cuda`
- `mace_precision = float64`
- `mace_use_dispersion = true`

### Where to patch

Patch the following manuscript locations:

- Method: physical backend paragraph
- Results: Adsorb-Agent matched-physics paragraph and MACE-MP-0 large sensitivity paragraph
- Discussion: operating-envelope / force-field-sensitivity paragraph
- SI captions: MACE-MP-0 small and MACE-MP-0 large table captions
- Data Availability: frozen configs and checkpoint-loading details

### Data Availability wording

Add a reproducibility note:

```latex
The primary calculator is loaded through \texttt{mace.calculators.mace\_mp} with the MACE-MP-0 small checkpoint, CPU execution, float32 precision, and dispersion disabled. The MACE-MP-0 large sensitivity runs use the large checkpoint, CUDA execution, float64 precision, and dispersion enabled. The corresponding frozen settings are archived in the experiment configuration files under \texttt{research/agent\_eval/configs/}.
```

Do not write exact parameter counts or `MACE-MP-0a` unless the actual remote checkpoint/version is confirmed.

## Citation Plan

### Current gap

`overleaf/refs.bib` includes `batatia2022mace`, which cites the MACE architecture, but it does not yet include the MACE-MP foundation model citation. The manuscript needs both:

- MACE architecture citation
- MACE-MP foundation model/checkpoint citation

### Add or verify citations

Add a `batatia2023foundation` BibTeX entry for the MACE-MP foundation model, then cite it wherever the physical backend is introduced.

Keep existing entries for:

- Adsorb-Agent paper
- CatalystAIgent/Adsorb-Agent implementation
- CHGNet
- EquiformerV2
- AdsorbML
- ChemCrow
- autonomous chemical research
- random/global optimization baselines

Do not delete unused references at this stage.

### Citation hints in text

Add citation anchors in:

- MLFF background sentence in Introduction
- MACE-MP physical backend sentence in Method
- Adsorb-Agent comparison paragraph in Results
- random/heuristic baseline paragraph in Results
- LLM chemistry agent background paragraph in Introduction

## Failure and N/A Definition Plan

### Problem

The manuscript currently risks mixing several meanings:

- `N/A`
- `NULL`
- not run
- no valid trajectory
- natural failure
- external service failure
- method out of scope

PI already asked what `N/A` means, so this must be clarified before figures/tables are finalized.

### Definitions

Use this taxonomy:

- `not run`: experiment was not included in that historical subset
- `natural failure`: execution/analyzer completed, but the relaxed structure is invalid, e.g. dissociation, reaction, or no valid relaxed adsorption configuration
- `external failure`: API quota, API error, network error, or service/runtime interruption
- `out of scope`: method does not support the dataset/task
- `NULL`: no valid adsorption energy or no valid trajectory in a reported run

### Statistical rules

- Natural failures stay in success-rate denominators.
- Natural failures are excluded from energy-delta statistics because no reliable energy exists.
- External failures are excluded from formal chemistry statistics and marked as blocked/retry-required.
- Historical not-run rows should not be counted as failures.
- Out-of-scope rows should not be counted as failures.

### Where to patch

- Results table captions involving `N/A` or `NULL`
- SI failure-aware table notes
- ablation summary captions
- any figure captions for success/failure markers

## Ablation Presentation Plan

### Main-text principle

The main text should not contain long raw ablation matrices. It should report the conclusion-level statistics and move detailed matrices/tests to SI.

Because the latest ablation/recovery batches are not yet all final, this section is a target structure rather than a final-number source. Any numerical claims in the manuscript must be regenerated from the final pulled datasets, not copied from interim reports.

Keep in main text:

- CMU20 Full success
- CMU20 1-Shot failure-aware drop
- OCD24 clean-backend summary
- rep50 Full-versus-1-Shot generalization
- key Full vs ablation-variant deltas
- matched baselines: random, heuristic, Adsorb-Agent
- MACE-MP-0 large sensitivity as a boundary condition

Move or keep in SI:

- per-backend raw energy matrices
- Wilcoxon/BH-FDR tables
- per-case full tables
- cost tables
- multi-seed checks
- detailed baseline tables
- failure taxonomy

### Figure-statistics direction

If Lou/PI converts the ablation table to a figure, use:

```latex
\Delta E = E_{\mathrm{variant}} - E_{\mathrm{full}}
```

Interpretation:

- positive values mean the variant is worse/higher energy than Full
- zero means tied with Full
- `+0.05 eV` can be used as a practical degradation threshold

Do not reuse the old Yes/No hit field as physical success/failure. The old Yes/No is an H1 hit test and has a different meaning.

Failures must be encoded separately from energy deltas, e.g. by:

- success-rate side panel
- failure rug marks
- red cross / N.A. markers
- separate failure table

## Introduction Revision Direction

The Introduction should move away from a technical-report style and follow a narrative arc:

1. Adsorption-configuration search is combinatorial and physically brittle.
2. MLFFs reduce per-evaluation cost but do not solve the search problem.
3. Existing LLM agents can propose structures, but single-shot or weakly feedback-conditioned proposals can silently fail.
4. AdsMind introduces a closed-loop feedback architecture for physically grounded correction.
5. Evidence should eventually come from CMU20, OCD24, rep50, matched baselines, MACE sensitivity, and DFT trajectory alignment. Until all final data are rebuilt, avoid hard-coding final counts in the Introduction unless they come from a locked, verified table.
6. The claim is not that AdsMind always finds the deepest MACE basin; the claim is reliability, efficiency, interpretability, and autonomous workflow readiness.

## Results Revision Direction

Results should be organized around claims rather than around every table:

1. Full closed-loop AdsMind improves reliability over 1-Shot.
2. Slip/FORBID/termination ablations identify which feedback channels matter.
3. Cross-backend consistency improves under the closed-loop setting.
4. OCD24 and rep50 show generalization beyond CMU.
5. Random/heuristic/Adsorb-Agent define the breadth-vs-depth boundary.
6. MACE-MP-0 large quantifies force-field sensitivity but does not provide DFT validation.
7. DFT trajectory alignment, once available, demonstrates application-level structural interpretability.

Current-stage rule: keep any not-yet-final expanded ablation, rep50, and recovery data in analysis notes or SI draft language until the final result pull and rebuild scripts have been run. Do not combine clean completed data with external-failure-blocked data in one formal table.

## Discussion Revision Direction

Discussion should make the operating envelope explicit:

- AdsMind is not a replacement for brute-force enumeration when compute is cheap and failures are tolerable.
- Brute-force methods can find lower MACE-MP-0 small energies in some cases.
- AdsMind's distinctive value is closed-loop recovery with fewer relaxations and inspectable failure modes.
- MACE-MP-0 small energies are an operational benchmark, not DFT truth.
- MACE-MP-0 large sensitivity shows that absolute energies can shift under a different force-field protocol.
- DFT application analysis should be used to discuss structure/trajectory agreement, not MACE-MP-0 small absolute-energy validation.

## Data Availability and Reproducibility Plan

Data Availability should mention:

- public code repository
- frozen configs
- manifests
- curated summary tables
- paper-facing LaTeX exports
- MACE protocol and checkpoint-loading path
- which outputs are archived summaries vs regenerable trajectory/log artifacts
- DFT data availability once Bowen/PI decide where to deposit it

Do not promise unavailable DFT artifacts before the final DFT package exists.

## Execution Order

### Current safe patch order

1. Terminology cleanup:
   - `Final Analyzer` to `Summarizer`
   - `post-relaxation Analyzer` to `Analyzer`
   - add code-level final analyzer node mapping if needed

2. MACE protocol patch:
   - Method
   - Results captions
   - Discussion
   - SI captions
   - Data Availability

3. Citation patch:
   - add MACE-MP foundation citation
   - add citation hints in main text
   - do not delete references

4. Failure/N/A taxonomy patch:
   - table captions
   - SI notes
   - Results paragraph explaining success-only energy deltas

### Defer until final experiment rebuild

5. Re-pull all completed remote result directories.
6. Rebuild final ablation summaries, baseline summaries, rep50 summaries, and failure audits.
7. Audit external-failure rows separately from natural failures.
8. Recompute all main-text numbers and SI tables from final rebuilt artifacts.
9. Ablation compression:
   - keep main text focused on mechanism conclusions;
   - move detailed raw matrices/statistics to SI;
   - update figure-facing data tables for Lou/PI.

10. DFT integration after data arrives:
   - add application paragraph
   - add DFT-alignment figure discussion
   - add SI alignment table

11. Rerun a final paper consistency check:
   - no stale 15-case language where 20-case final data are used;
   - no Grok/Gemini external-failure rows mixed into clean statistics;
   - no DFT claims based only on the MVP package;
   - all table captions match the final denominator.

## Final Checklist

- No remaining `Final Analyzer` in manuscript text.
- `Analyzer` and `Summarizer` have separate functions.
- MACE is written as MACE-MP-0 small/large where relevant.
- No accidental MACE-OFF wording.
- MACE-MP foundation model citation exists.
- `N/A`, `NULL`, natural failure, external failure, and out-of-scope are not conflated.
- External API failures are excluded from formal chemistry statistics.
- Natural failures remain in success-rate denominators.
- Energy deltas are success-only where no valid failed-run energy exists.
- MACE-MP-0 large is not described as DFT validation.
- Abstract and placeholders are left untouched unless explicitly requested.
- Extra references are not deleted.
- Unfinished experiments are not described as completed.
