# AdsMind paper artifacts — v0.1.0 (DRAFT)

Release notes for the artifact archive accompanying the AdsMind preprint
(arXiv:2606.19152). **Draft**: finalize and attach the archive zip when ready.

## Provenance

| Field | Value |
|---|---|
| AdsMind version | 0.1.0 |
| Source commit | `6fb134a9` (update before tagging the release) |
| Python | `>=3.10,<3.12` (see `pyproject.toml` / `uv.lock`) |
| Platform | CPU (primary protocol); CUDA used only for the MACE-MP-0 (large) sensitivity check |
| MLFF — primary | MACE-MP-0 (small), float32, dispersion disabled, BFGS `f_max=0.10` eV/Å, ≤200 steps, bottom one-third of slab fixed |
| MLFF — sensitivity | MACE-MP-0 (large), CUDA, float64, dispersion enabled |
| DFT reference | VASP 6.4.2, PBE, PAW, VASPKIT 1.5.1 (six representative AA20 systems) |
| LLM backends (temperature 0) | Gemini-2.5-Pro, GPT-5.4, Claude-Sonnet-4.6, Grok-4 |
| Credentials | none included — API keys / provider credentials are excluded |

## What is committed vs. archived

- **Committed in the repository** (sufficient to reproduce every reported
  number): benchmark manifests (`datasets/`), frozen run configurations
  (`research/agent_eval/configs/`), reproduction scripts
  (`research/agent_eval/`, `research/analysis/`), and path-sanitized summaries /
  per-case records (`research/results/`).
- **In this archive** (excluded from the clone to keep it small): raw relaxation
  trajectories, full per-run artifacts, agent/driver logs, and high-resolution
  figure sources.

## Which files back each paper element

| Paper element | Location |
|---|---|
| DFT validation, six AA20 systems (Fig. 2 / SI DFT table) | `research/results/advanced_experiments/case_studies/dft_iteration_alignment/` |
| AA20 five-variant × four-backend ablation (Fig. 3 / SI) | `research/results/basic_experiments/cmu20/adsmind/<backend>/all_variants_summary.csv`; `…/summaries/cmu20_ablation_4backend.csv` |
| AA20 convergence, Chemical-Slip, backend heatmap (Fig. 4 / SI) | `…/advanced_experiments/case_studies/iteration_convergence/`; `…/ablation_and_chemical_slip_diagnostics/` |
| Heuristic + Adsorb-Agent baseline comparison | `…/basic_experiments/{cmu20,ocd62}/baselines/heuristic/`; `…/summaries/method_comparison_table.md`; `research/agent_eval/compare_adsorbagent.py` |
| Per-agent ablation (AA20) | `…/advanced_experiments/ablation_and_chemical_slip_diagnostics/per_agent_ablation/` |
| OCD-GMAE62 Tier-1 (Table 1 / SI) | `…/basic_experiments/ocd62/adsmind/<backend>/all_variants_summary.csv`; `…/summaries/ocd62_ablation_4backend.csv` |
| OCD-GMAE62 Tier-2 N=3 stability (Fig. 5 / SI) | `…/advanced_experiments/reproducibility/ocd62_overlap12_rerun/summaries/reproducibility_n3.csv`, `reproducibility_n3_minvar.csv` |
| MACE-MP-0 small-vs-large sensitivity (SI) | `…/advanced_experiments/force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/` |

## Integrity

SHA-256 checksums for the committed promoted inputs (manifests + headline
summary tables) are in [`checksums.txt`](checksums.txt); verify with
`shasum -a 256 -c paper-artifacts/checksums.txt` from the repository root. Append
the archive-payload checksums to that file when the zip is built.

## Archive layout (to assemble)

```text
adsmind-paper-artifacts-v0.1.0/
  README.md            # this provenance summary
  checksums.txt        # extended with raw-payload hashes
  results/
    basic_experiments/     # cmu20 + ocd62 AdsMind/baseline summaries (mirrors research/results/)
    advanced_experiments/  # ablation+slip, force-field sensitivity, reproducibility, case studies
  trajectories/        # raw relaxation trajectories (not in the clone)
  figures/             # high-resolution figure sources
  provenance/          # frozen configs, environment lock, run logs
```
