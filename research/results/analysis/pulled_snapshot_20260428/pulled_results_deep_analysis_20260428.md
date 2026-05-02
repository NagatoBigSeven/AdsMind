# Pulled Remote Results Deep Analysis — 2026-04-28

## Executive Summary

- Remote-to-local sync completed: all remote result directories are now present locally; 21 previously missing result directories plus run logs/configs were pulled.
- No active remote experiment process was observed during the check; remaining work is data merge/QC, not waiting for a running job.
- Main conclusion: after replacing external-failure rows with targeted recovery outputs, the CMU20/OCD24/rep50 ablation datasets are analyzable. No mandatory immediate rerun is required for the main ablation statistics.
- Important caveat: several recovery summaries are incomplete or mislabeled relative to their result-json subdirectories. Formal statistics must be rebuilt from result.json, not by concatenating ablation_summary.csv files blindly.
- Natural failures remain and should be counted as failures, not hidden: OCD24 Grok-4 single-shot cases 009 and 011; rep50 case 043 for several backend/variant combinations; P8 single-config control has no-selected-config cases.

## Data Pulled

- Added local directories: 21 result directories. The most important additions are rep50 baselines, seed47 multiseed, Grok-4/Gemini recovery batches, and DFT visualization case01 outputs.
- Also updated: run logs and run configs for failure provenance.

## Completeness After Clean Merge

### OCD24 Four-Backend Ablation

|backend|variant|total|valid_success|natural_failure|external_failure|invalid_energy|
|---|---|---|---|---|---|---|
|Claude Sonnet 4.6|full|24|24|0|0|0|
|Claude Sonnet 4.6|no_forbid|24|24|0|0|0|
|Claude Sonnet 4.6|no_slip|24|24|0|0|0|
|Claude Sonnet 4.6|no_termination|24|24|0|0|0|
|Claude Sonnet 4.6|single_shot|24|22|2|0|0|
|GPT-5.4|full|24|24|0|0|0|
|GPT-5.4|no_forbid|24|24|0|0|0|
|GPT-5.4|no_slip|24|24|0|0|0|
|GPT-5.4|no_termination|24|23|1|0|0|
|GPT-5.4|single_shot|24|19|5|0|0|
|Gemini 2.5 Pro|full|24|24|0|0|0|
|Gemini 2.5 Pro|no_forbid|24|24|0|0|0|
|Gemini 2.5 Pro|no_slip|24|24|0|0|0|
|Gemini 2.5 Pro|no_termination|24|24|0|0|0|
|Gemini 2.5 Pro|single_shot|24|20|4|0|0|
|Grok-4|full|24|24|0|0|0|
|Grok-4|no_forbid|24|24|0|0|0|
|Grok-4|no_slip|24|24|0|0|0|
|Grok-4|no_termination|24|24|0|0|0|
|Grok-4|single_shot|24|21|3|0|0|

### OCD rep50 Full Variant

|backend|variant|total|valid_success|natural_failure|external_failure|invalid_energy|
|---|---|---|---|---|---|---|
|Claude Sonnet 4.6|full|50|50|0|0|0|
|GPT-5.4|full|50|49|1|0|0|
|Gemini 2.5 Pro|full|50|49|1|0|0|
|Grok-4|full|50|49|1|0|0|

### OCD rep50 Mechanism Variants

|backend|variant|total|valid_success|natural_failure|external_failure|invalid_energy|
|---|---|---|---|---|---|---|
|Claude Sonnet 4.6|no_forbid|50|49|1|0|0|
|Claude Sonnet 4.6|no_slip|50|50|0|0|0|
|Claude Sonnet 4.6|no_termination|50|50|0|0|0|
|GPT-5.4|no_forbid|50|49|1|0|0|
|GPT-5.4|no_slip|50|49|1|0|0|
|GPT-5.4|no_termination|50|49|1|0|0|
|Gemini 2.5 Pro|no_forbid|50|50|0|0|0|
|Gemini 2.5 Pro|no_slip|50|50|0|0|0|
|Gemini 2.5 Pro|no_termination|50|50|0|0|0|
|Grok-4|no_forbid|50|50|0|0|0|
|Grok-4|no_slip|50|50|0|0|0|
|Grok-4|no_termination|50|50|0|0|0|


## Success-Only Delta vs Full

Positive delta means the ablated variant is higher in energy and therefore worse than Full. These deltas are success-only; natural failures must be shown separately as failure counts/rug marks/N.A. rather than silently dropped.

### OCD24

|backend|variant|n|mean|median|worse_gt_0p05|better_lt_minus0p05|within_0p05|
|---|---|---|---|---|---|---|---|
|Claude Sonnet 4.6|no_forbid|24|-0.004833221435546875|0.0|1|2|21|
|Claude Sonnet 4.6|no_slip|24|-0.007644494374593099|0.0|3|3|18|
|Claude Sonnet 4.6|no_termination|24|-0.02425543467203776|0.0|1|4|19|
|Claude Sonnet 4.6|single_shot|22|0.4285546216097745|0.11053466796875|12|0|10|
|GPT-5.4|no_forbid|24|0.10959291458129883|0.0|5|0|19|
|GPT-5.4|no_slip|24|0.10982139905293782|6.103515625e-05|5|0|19|
|GPT-5.4|no_termination|23|0.02424347918966542|0.0|2|0|21|
|GPT-5.4|single_shot|19|0.31695877878289475|0.01499176025390625|9|0|10|
|Gemini 2.5 Pro|no_forbid|24|0.01678466796875|0.0|4|1|19|
|Gemini 2.5 Pro|no_slip|24|-0.024507522583007812|0.0|2|4|18|
|Gemini 2.5 Pro|no_termination|24|0.028070767720540363|0.0|3|0|21|
|Gemini 2.5 Pro|single_shot|20|0.2549869537353516|0.04223823547363281|10|0|10|
|Grok-4|no_forbid|24|-0.06151580810546875|0.0|0|3|21|
|Grok-4|no_slip|24|-0.024856011072794598|0.0|4|4|16|
|Grok-4|no_termination|24|-0.07686996459960938|0.0|1|3|20|
|Grok-4|single_shot|21|0.21159408206031435|0.000244140625|9|0|12|

### OCD rep50

|backend|variant|n|mean|median|worse_gt_0p05|better_lt_minus0p05|within_0p05|
|---|---|---|---|---|---|---|---|
|Claude Sonnet 4.6|no_forbid|49|0.001869727154167331|0.0|8|6|35|
|Claude Sonnet 4.6|no_slip|50|0.05907993316650391|0.0|10|9|31|
|Claude Sonnet 4.6|no_termination|50|-0.07232057571411132|0.0|7|6|37|
|GPT-5.4|no_forbid|49|0.009882596074318399|0.0|6|7|36|
|GPT-5.4|no_slip|49|-0.04333034826784718|0.0|4|8|37|
|GPT-5.4|no_termination|49|-0.07832840510777064|0.0|2|10|37|
|Gemini 2.5 Pro|no_forbid|49|0.016487549762336576|0.0|7|4|38|
|Gemini 2.5 Pro|no_slip|49|0.045315178073182395|0.0|8|4|37|
|Gemini 2.5 Pro|no_termination|49|-0.02091283214335539|0.0|1|8|40|
|Grok-4|no_forbid|49|-0.012780208976901308|0.0|4|6|39|
|Grok-4|no_slip|49|0.03597786961769571|0.0|9|7|33|
|Grok-4|no_termination|49|0.005269186837332589|0.0|7|8|34|


## Non-Valid Selected Records

These are not external API failures after clean merge. They are natural/no-valid-configuration outcomes unless noted otherwise.

|dataset|backend|variant|case_id|class_|recommended_action|note|
|---|---|---|---|---|---|---|
|OCD24|Claude Sonnet 4.6|single_shot|009|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Claude Sonnet 4.6|single_shot|011|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Gemini 2.5 Pro|single_shot|002|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Gemini 2.5 Pro|single_shot|009|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Gemini 2.5 Pro|single_shot|011|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Gemini 2.5 Pro|single_shot|022|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|GPT-5.4|no_termination|008|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|GPT-5.4|single_shot|002|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|GPT-5.4|single_shot|009|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|GPT-5.4|single_shot|011|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|GPT-5.4|single_shot|017|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|GPT-5.4|single_shot|022|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Grok-4|single_shot|009|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Grok-4|single_shot|011|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|OCD24|Grok-4|single_shot|022|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-full|Gemini 2.5 Pro|full|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-full|GPT-5.4|full|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-full|Grok-4|full|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-mechanism|Claude Sonnet 4.6|no_forbid|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-mechanism|GPT-5.4|no_slip|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-mechanism|GPT-5.4|no_forbid|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|
|rep50-mechanism|GPT-5.4|no_termination|043|natural_failure|do_not_rerun_count_as_natural|Selected merged record has no valid energy.|


## Records That Must Not Enter Formal Stats Unfiltered

- Several raw candidate rows are external failures or numerical-invalid success rows. They are superseded by recovery/older valid records where possible.
- Notable invalid-energy case: OCD24 Grok-4 case 008 has absurdly large negative energies in some raw runs. Use the valid original Full row and the targeted valid no-forbid recovery row; do not use the invalid rows.
- For Grok-4 and Gemini rep50 mechanism, recovery result_json files complete the matrix, but summary CSVs alone do not expose all recovered rows correctly.

## Supplemental Experiment Decision

- Mandatory rerun now: none for the main CMU20/OCD24/rep50 ablation story, provided we rebuild clean merged tables from result_json.
- Do not rerun merely to erase natural failures; doing so would bias the failure-rate story. If a figure demands a full numeric energy matrix, mark these as N.A./failure and plot success rate separately.
- Optional rerun only if the team explicitly wants stochastic repeat evidence: OCD24 Grok-4 single-shot cases 009/011; rep50 case 043 in failed backend/variant combinations; P8 single-config control no-selected-config cases. These should be labeled as repeat controls, not replacement of first-pass failure statistics.

## Auxiliary Data Status

- OCD rep50 random baseline: 50 rows
- OCD rep50 heuristic baseline: 50 rows
- OCD24 heuristic baseline: 24 rows
- P6 GPT-5.4 multiseed seed47: 20 rows
- P8 single-config AA control: 20 rows

## Files Written

- `research/results/analysis/pulled_snapshot_20260428/ocd24_merged_qc.csv`
- `research/results/analysis/pulled_snapshot_20260428/rep50_full_merged_qc.csv`
- `research/results/analysis/pulled_snapshot_20260428/rep50_mechanism_merged_qc.csv`
- `research/results/analysis/pulled_snapshot_20260428/ocd24_delta_summary_success_only.csv`
- `research/results/analysis/pulled_snapshot_20260428/rep50_delta_summary_success_only.csv`
- `research/results/analysis/pulled_snapshot_20260428/non_valid_selected_records.csv`
- `research/results/analysis/pulled_snapshot_20260428/invalid_or_external_candidate_records.csv`
