# Artifact Layout Audit 2026-05-02

## Scope

This audit checks why canonical raw result directories do not all contain the same structure files. It focuses on `research/results/canonical_raw/` and excludes `superseded_raw_sources/` from active completeness decisions.

## Main Findings

The layout differences are mostly expected:

- AdsMind ablation runs store `variant/case/result.json` and, when the run reached physical execution, `variant/case/artifacts/`.
- A full AdsMind run can contain many `.xyz` files because each iteration may save a current best or diagnostic structure, plus `final.xyz` and trajectory files.
- Random and heuristic baselines store only top structures, usually about three `.xyz` files per case, and do not use the same `artifact_paths` schema.
- CatalystAIgent / Adsorb-Agent controls use their own `summary.csv`, `.pkl`, and `.traj` layout rather than AdsMind-style per-case `result.json`.

## Fixed During This Audit

`ocd_rep50_*_ablation/single_shot/*/result.json` files had path strings missing the `single_shot/` directory component. The structure files were present locally, but the JSON paths pointed to non-existent locations.

Fixed:

- `ocd_rep50_anthropic_sonnet46_ablation`: 50 `single_shot` result JSON files
- `ocd_rep50_gemini_ablation`: 50 `single_shot` result JSON files
- `ocd_rep50_grok4_ablation`: 50 `single_shot` result JSON files
- `ocd_rep50_openai_gpt54_ablation`: 50 `single_shot` result JSON files

After the rewrite, the rep50 single-shot artifact paths resolve locally.

## Remaining Missing Artifact Files

The active missing artifact references are now concentrated in early CMU Gemini/Grok runs:

| directory | missing artifact refs | affected result.json files | cause |
|---|---:|---:|---|
| `cmu20_gemini_ablation` | 392 | 25 | original early source retained `result.json` only for cases 01, 02, 09, 14, 19 |
| `cmu20_grok4_ablation` | 340 | 20 | original early source retained `result.json` only for cases 01, 02, 09, 14, 19 |
| `legacy_raw_sources/cmu20_gemini_one_shot` | 200 | 20 | legacy provenance source retained one-shot `result.json` only |
| `legacy_raw_sources/cmu20_grok4_progressive_one_shot` | 200 | 20 | legacy provenance source retained one-shot `result.json` only |

I checked LIAC remote source directories directly. For example, the following remote directories also contain only `result.json` and no `artifacts/`:

- `research/results/gemini_ablation_v1/full/01`
- `research/results/gemini_ablation_v1/no_forbid/01`
- `research/results/gemini_ablation_v1/single_shot/01`
- `research/results/xai_ablation_v2/full/01`

So these are not local-copy omissions.

## Zero-Artifact Runs

Some active directories have `zero_artifact_ref_result_json_count > 0`. These are not missing files. They are raw runs that never reached physical artifact generation, typically due to external API failures such as billing, quota, or provider overload.

Examples visible in the raw JSON status/error fields:

- `ocd24_grok4_ablation`: API quota/billing failures.
- `ocd_rep50_gemini_ablation`: Vertex billing failures.
- `ocd_rep50_grok4_ablation`: API quota failures.
- `ocd_rep50_anthropic_sonnet46_ablation`: provider overload failures.

These should be handled as failed raw runs or excluded according to the analysis protocol, not treated as missing `.xyz` files.

## QC Updates

`research/agent_eval/rebuild_canonical_raw_qc.py` now writes artifact completeness fields into `research/results/canonical_raw/MERGE_QC.csv`:

- `xyz_count`
- `traj_count`
- `artifact_ref_count`
- `missing_artifact_ref_count`
- `zero_artifact_ref_result_json_count`
- `missing_artifact_ref_result_json_count`

Rebuild command:

```bash
python3 research/agent_eval/rebuild_canonical_raw_qc.py
```

