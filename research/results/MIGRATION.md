# research/results/ Migration Notes

History of structural cleanups applied to this directory.

---

## 2026-05-02 — Round 4 cleanup (version/date-label governance)

Added machine-readable registries so compact backend names, date-stamped
analysis exports, and manifest-version labels no longer have to be interpreted
from path names alone.

New files:

- `RUN_REGISTRY.csv` — 42 rows covering canonical raw result sources plus the
  retained root-level `adsorbagent_mace_gpt54/` comparison source.
- `ANALYSIS_REGISTRY.csv` — 65 rows covering first-level artifacts under
  `analysis/`.
- `REGISTRY.md` — naming policy and registry usage guide.
- `research/agent_eval/rebuild_result_registries.py` — deterministic rebuild
  script for both registries.

Policy decisions:

- Kept existing paper-facing paths stable; no raw result or analysis directory
  was renamed in this round.
- Backend slugs such as `openai_gpt54`, `anthropic_sonnet46`, `gemini`, and
  `grok4` are now treated as stable labels only. Exact model IDs and transports
  are resolved through `RUN_REGISTRY.csv`.
- Date tokens under `analysis/` are historical snapshot labels, not authority
  or recency signals. `ANALYSIS_REGISTRY.csv` records `category` and
  `preferred_status` for citation decisions.
- Future `vN`, `retry`, or `dryrun` labels must be paired with registry metadata
  or a migration note instead of standing alone.

Audit signals captured in the registries:

| Signal | Count |
|---|---:|
| Raw/result registry rows | 42 |
| Analysis registry rows | 65 |
| Run rows flagged `mixed_model_ids` | 4 |
| Analysis rows flagged `date_token` | 17 |
| Analysis rows with host-specific path matches | 5 |
| Host-specific matches inside analysis registry scope | 104 |

The host-path matches above are historical analysis artifacts, not canonical
raw JSON/CSV data; Round 3 already verified zero matches in active canonical
raw data and `adsorbagent_mace_gpt54/`.

Rebuild command:

```bash
python3 research/agent_eval/rebuild_result_registries.py
```

---

## 2026-05-02 — Round 3 cleanup (canonical raw host-path sanitization)

Removed host-specific absolute AdsMind workspace prefixes from canonical JSON/CSV
data under:

- `research/results/canonical_raw/`
- `research/results/adsorbagent_mace_gpt54/`

The cleanup is implemented by
`research/agent_eval/sanitize_canonical_paths.py`, which walks only `*.json`
and `*.csv` under those two roots, skips `agent_log.txt`, and strips these
prefix classes while preserving all other bytes:

- `/data/zongmin/workspace/AdsMind/`
- `/Users/nagato/workspace/AdsMind/`
- `/home/<dev-user>/workspace/AdsMind/`

Run result:

| Metric | Count |
|---|---:|
| Files scanned | 5904 |
| Files changed | 647 |
| `/data/zongmin/...` replacements | 9718 |
| `/Users/nagato/...` replacements | 564 |
| `/home/<dev-user>/...` replacements | 0 |
| Total replacements | 10282 |

`agent_log.txt` traceback noise was intentionally left untouched. Future
canonical merges now strip the same host prefixes in
`research/agent_eval/maintenance_merge_split_result_dirs.py` before rewriting
split-run paths to canonical paths.

Verification:

- A post-run `--dry-run` reported 0 remaining replacements.
- A byte comparison against a pre-run JSON/CSV snapshot confirmed every changed
  file equals the original content with only the sanitizer applied.
- `research/agent_eval/rebuild_canonical_raw_qc.py` rebuilt
  `canonical_raw/MERGE_QC.csv` byte-identically.
- Final grep count: 0

```bash
grep -rE "/(data/zongmin|Users/nagato|home/[a-z_]+)/workspace/AdsMind" \
  research/results/canonical_raw research/results/adsorbagent_mace_gpt54 \
  --include="*.json" --include="*.csv" | wc -l
```

---

## 2026-04-30 — Round 2 cleanup (post-Codex consolidation)

Builds on Codex's 2026-04-29 `Consolidate canonical raw experiment results`
commit (`a9f4a03`). Codex created the `canonical_raw/` layer and merged
same-protocol split runs; this round closes the remaining gaps:

1. Resolved 6 leftover top-level dirs (decisions table below).
2. Moved 14 loose paper-derived files at root into `analysis/`.
3. Removed back-compat symlinks under `research/agent_eval/generated_slabs/`
   after rewriting their references in analysis JSON/CSV.

### Decisions for the 6 leftover top-level dirs

| Dir | Decision | Reason |
|---|---|---|
| `adsorbagent_mace_gpt54/` | **KEEP at root** | Paper-cited 7+ times in README (main AdsMind vs Adsorb-Agent comparison source). Moving it would break the published reference path. |
| `adsorbagent_mace_gpt4o/` | **→ `canonical_raw/auxiliary_raw/`** | README labels it "Historical GPT-4o comparison". Auxiliary, not paper-citation-critical. |
| `mace_large_gpt54/` | **Superseded by `canonical_raw/controls/mace_large_gpt54_cmu20_full/` and `canonical_raw/controls/mace_large_gpt54_ocd_rep10_full/`** | The old 5-case sensitivity snapshot is incomplete. The active paper-facing controls are the CMU20 full-only and OCD rep10 full-only MACE-large directories under `canonical_raw/controls/`. |
| `multiseed_gpt54/` | **Superseded by `canonical_raw/controls/multiseed_gpt54_cmu20_seed{43,44,45,46,47}_full/`** | The old auxiliary snapshot had fewer seeds/cases. The active control is the five-seed CMU20 full-only set under `canonical_raw/controls/`. |
| `adsorbagent_single_config_gpt54_cmu20/` | **→ `canonical_raw/controls/adsorbagent_single_config_gpt54_cmu20/`** | Active AA single-config control used by the manuscript/SI discussion. It is cited through inlined analysis rather than direct grep-visible file references, so it must remain active rather than superseded. |
| `catalystaigent_remote_results/` | **→ `canonical_raw/superseded_raw_sources/`** | Zero references anywhere. Holds older `cmu_benchmark*` runs from the CatalystAIgent baseline tool; superseded by current `canonical_raw/cmu20_*_ablation/` and `cmu20_random_baseline_n20/`. Retained for audit. |

### Loose top-level files moved to `analysis/`

All paper-derived analysis outputs and SI exports (referenced from
`README.md` and `README_CN.md` only — no .py code paths). Both READMEs were
updated in the same pass to point to the new `analysis/<name>` paths.

| File | New path |
|---|---|
| `cross_llm_ablation_4backend.json` | `analysis/cross_llm_ablation_4backend.json` |
| `hypothesis_test.json` | `analysis/hypothesis_test.json` |
| `key_evaluation_metrics.json` | `analysis/key_evaluation_metrics.json` |
| `ocd_gmae_ablation_final_vs_one_shot_4backend.csv` | `analysis/ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |
| `ocd_gmae_ablation_multi_backend_final.csv` | `analysis/ocd_gmae_ablation_multi_backend_final.csv` |
| `ocd_gmae_ablation_multi_backend_final.json` | `analysis/ocd_gmae_ablation_multi_backend_final.json` |
| `ocd_gmae_one_shot_top_10_case_ids.txt` | `analysis/ocd_gmae_one_shot_top_10_case_ids.txt` |
| `ocd_gmae_paper_tables.tex` | `analysis/ocd_gmae_paper_tables.tex` |
| `paper_tables.tex` | `analysis/paper_tables.tex` |
| `si4_ablation_statistics.json` | `analysis/si4_ablation_statistics.json` |
| `si4_ablation_statistics.tex` | `analysis/si4_ablation_statistics.tex` |
| `si4_ocd_gmae_ablation_statistics.json` | `analysis/si4_ocd_gmae_ablation_statistics.json` |
| `si4_ocd_gmae_ablation_statistics.tex` | `analysis/si4_ocd_gmae_ablation_statistics.tex` |
| `si6_cost_analysis.json` | `analysis/si6_cost_analysis.json` |
| `si6_cost_analysis.tex` | `analysis/si6_cost_analysis.tex` |
| `si_adsorbagent_comparison.tex` | `analysis/si_adsorbagent_comparison.tex` |
| `si_baselines_comparison.tex` | `analysis/si_baselines_comparison.tex` |
| `si_iteration_convergence.tex` | `analysis/si_iteration_convergence.tex` |
| `si_mace_sensitivity.tex` | `analysis/si_mace_sensitivity.tex` |

### Symlink removal

Removed (generated_slabs/, 2026-04-30):
- `research/agent_eval/generated_slabs/ocd_gmae` → was → `ocd_gmae_subset24`
- `research/agent_eval/generated_slabs/ocd_gmae_rep50` → was → `ocd_gmae_representative50`

Removed (manifests/, 2026-05-02 — second pass after final audit):
- `research/agent_eval/manifests/ocd_gmae_manifest.csv` → was → `ocd_gmae_subset24_manifest.csv`
- `research/agent_eval/manifests/ocd_gmae_manifest_selection.json` → was → `ocd_gmae_subset24_manifest_selection.json`
- `research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv` → was → `ocd_gmae_representative50_manifest.csv`
- `research/agent_eval/manifests/ocd_gmae_rep50_manifest_selection.json` → was → `ocd_gmae_representative50_manifest_selection.json`

All four manifest symlinks had **0 references** anywhere in the repo (.py/.md/.csv/.json) — pure dead compatibility shims paired with the already-removed `generated_slabs/` symlinks.

`ocd_gmae_rep50` had **0 path references** anywhere — pure dead symlink.
`ocd_gmae` had **34 path references** in 2 analysis files
(`research/results/analysis/ocd_gmae_one_shot_range_ranking.{json,csv}`); these
were rewritten in-place to point to the canonical `ocd_gmae_subset24/` target,
and `research/agent_eval/generated_slabs/README.md` updated to drop the
"compatibility symlinks" section.

### What's intentionally NOT done in this round (deferred)

- Read-only data layer (`chmod -R a-w canonical_raw/`)
- SHA256 in `MERGED_SOURCES.json`
- Per-canonical-dir mini-READMEs
- `paper_v1_data_lock.txt` snapshot
- Schema-version field in `result.json`
- Cross-link between `run_configs/` and `canonical_raw/`

Track these for the next cleanup round.
