# Pulled Results Deep Analysis — 2026-04-26

## Scope

本报告分析本轮已拉回本地的数据，并显式区分三类状态：科学成功、自然/物理失败、外部服务失败。文件数完整不等于科学数据完整；所有正式统计都不能把 API/billing/overload 失败当作物理失败。

仍在远程运行、未纳入本轮正式统计的数据：Grok rep50 mechanism 余量、P6 seed47、OCD24 heuristic baseline 最后 1 个 case。

## Inventory

| dataset | path | total_result_json | summaries |
| --- | --- | --- | --- |
| OCD24 Grok recovery no_term duplicate+single_shot | research/results/ocd_gmae_24_extra14_grok4_openrouter_recovery | 26 | ablation_summary.csv |
| OCD24 Grok dedicated single_shot recovery | research/results/ocd_gmae_24_extra14_grok4_openrouter_single_shot_recovery | 13 | ablation_summary.csv |
| rep50 OpenAI mechanism | research/results/ocd_gmae_rep50_openai_gpt54_mechanism | 150 | ablation_summary.csv |
| rep50 Claude mechanism | research/results/canonical_raw/ocd_rep50_anthropic_sonnet46_ablation | 150 | ablation_summary.csv |
| rep50 Gemini mechanism | research/results/canonical_raw/ocd_rep50_gemini_ablation | 150 | ablation_summary.csv |
| P6 GPT multiseed seed43 | research/results/canonical_raw/controls/multiseed_gpt54_cmu20_seed43_full | 20 | ablation_summary.csv |
| P6 GPT multiseed seed44 | research/results/canonical_raw/controls/multiseed_gpt54_cmu20_seed44_full | 20 | ablation_summary.csv |
| P6 GPT multiseed seed45 | research/results/canonical_raw/controls/multiseed_gpt54_cmu20_seed45_full | 20 | ablation_summary.csv |
| P6 GPT multiseed seed46 | research/results/canonical_raw/controls/multiseed_gpt54_cmu20_seed46_full | 20 | ablation_summary.csv |
| OCD24 random n=20 baseline | research/results/random_baseline_ocd24_n20 | 24 | summary.csv;summary.json |


## Data-Quality Findings

- `result.json` 计数全部通过，但有两个重要质量问题必须在统计口径里处理。

- OCD24 Grok case008 `no_forbid` 有一个不可能的吸附能 `-3.985e8 eV`，伴随 0.312 Å 的 N--Sc 接触；我已把它重分类为 `invalid_physical_result`，不进入 success 或能量均值。

- rep50 Gemini mechanism 的 `no_termination` 是 50/50 外部 billing failure；Gemini `no_forbid` 有 33/50 外部 billing failure；Claude `no_slip` 有 12/50 外部 overload failure。这些不能写成模型/算法失败。

Invalid physical-result rows：

| backend | case_id | variant | best_energy | source | reason |
| --- | --- | --- | --- | --- | --- |
| Grok-4 | 008 | no_forbid | -398501376.734 | extra14 | absurd_adsorption_energy_outside_-100_to_20_eV |


## OCD24 Grok Recovery Audit

- 原始 Grok extra14 `single_shot` 有 9 个外部 429/credit 失败。dedicated recovery 覆盖 13 个 case，其中 11 个成功、2 个自然失败；case 017 仍是外部缺口。

- `no_termination` recovery 是重复运行：原始 extra14 已成功；13 个重复 case 的 recovery-minus-original 平均 0.034 eV，中位 0.000 eV，最大绝对差 0.428 eV。因此我没有用 recovery 覆盖原始成功结果。

- 两套 single-shot recovery 在 11 个双成功 case 上平均差 -0.001 eV，最大绝对差 0.145 eV；case011 一套成功、一套自然失败，不能选择性挑成功结果。



## OCD24 Four-Backend Ablation After Recovery

口径：原始成功保留；只有原始外部失败才用 recovery 替换；自然失败、invalid physical result、外部失败分别计数。Δ = `E_variant - E_full`，正值表示 variant 更差。

| variant | attempts | success | natural_failures | invalid_failures | external_failures | success_rate_excluding_external | mean_delta_vs_full_success_only_eV | median_delta_vs_full_success_only_eV | reach_or_beat_full_plus_0p01_including_failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full | 96 | 96 | 0 | 0 | 0 | 100.0% | 0.000 | 0.000 | 96 |
| no_slip | 96 | 96 | 0 | 0 | 0 | 100.0% | 0.013 | 0.000 | 76 |
| no_forbid | 96 | 95 | 0 | 1 | 0 | 99.0% | 0.015 | 0.000 | 80 |
| no_termination | 96 | 95 | 1 | 0 | 0 | 99.0% | -0.013 | 0.000 | 81 |
| single_shot | 96 | 82 | 13 | 0 | 1 | 86.3% | 0.315 | 0.060 | 33 |

Case-best-of-4 视角：

| variant | cases | cases_with_success | mean_delta_casebest_success_only | median_delta_casebest_success_only | reach_or_beat_full_plus_0p01_cases |
| --- | --- | --- | --- | --- | --- |
| full | 24.000 | 24.000 | 0.000 | 0.000 | 24.000 |
| no_forbid | 24.000 | 24.000 | -0.004 | 0.000 | 22.000 |
| no_slip | 24.000 | 24.000 | 0.017 | 0.000 | 21.000 |
| no_termination | 24.000 | 24.000 | 0.021 | 0.000 | 20.000 |
| single_shot | 24.000 | 22.000 | 0.244 | 0.018 | 9.000 |


Interpretation: Full / `no_slip` 均 96/96 成功；`no_forbid` 只有 1 个 invalid physical result；`no_termination` 1 个自然失败；`single_shot` 82/95 scientific attempts 成功，另有 1 个外部缺口。closed-loop 相对 single-shot 的可靠性优势仍然成立。



## rep50 Mechanism Ablation — File-Complete, Scientifically Partial

三后端 mechanism 目录都有 150 个 result 文件，但其中 95 个是外部服务失败，不应进入科学统计。下面表格同时给出 attempts 与 external failures；success rate 用 excluding external 口径。Grok rep50 mechanism 仍在远程运行，未纳入。

| variant | attempts | success | natural_failures | invalid_failures | external_failures | scientific_attempts_excluding_external | success_rate_excluding_external | paired_success | mean_delta_vs_full_success_only_eV | median_delta_vs_full_success_only_eV | reach_or_beat_full_plus_0p01_including_failures | wilcoxon_p_delta_vs_full |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_forbid | 150 | 115 | 2 | 0 | 33 | 117 | 98.3% | 115 | 0.018 | 0.000 | 92 | 0.995 |
| no_slip | 150 | 137 | 1 | 0 | 12 | 138 | 99.3% | 136 | 0.019 | 0.000 | 111 | 0.708 |
| no_termination | 150 | 99 | 1 | 0 | 50 | 100 | 99.0% | 99 | -0.075 | 0.000 | 84 | 0.046 |

Backend-level breakdown：

| backend | variant | attempts | success | natural_failures | external_failures | scientific_attempts | paired_success | mean_delta | median_delta | reach_full_0p01 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Sonnet 4.6 | no_forbid | 50.000 | 49.000 | 1.000 | 0.000 | 50.000 | 49.000 | 0.002 | 0.000 | 41.000 |
| Claude Sonnet 4.6 | no_slip | 50.000 | 38.000 | 0.000 | 12.000 | 38.000 | 38.000 | 0.064 | 0.000 | 30.000 |
| Claude Sonnet 4.6 | no_termination | 50.000 | 50.000 | 0.000 | 0.000 | 50.000 | 50.000 | -0.072 | 0.000 | 41.000 |
| GPT-5.4 | no_forbid | 50.000 | 49.000 | 1.000 | 0.000 | 50.000 | 49.000 | 0.010 | 0.000 | 39.000 |
| GPT-5.4 | no_slip | 50.000 | 49.000 | 1.000 | 0.000 | 50.000 | 49.000 | -0.043 | 0.000 | 44.000 |
| GPT-5.4 | no_termination | 50.000 | 49.000 | 1.000 | 0.000 | 50.000 | 49.000 | -0.078 | -0.000 | 43.000 |
| Gemini 2.5 Pro | no_forbid | 50.000 | 17.000 | 0.000 | 33.000 | 17.000 | 17.000 | 0.091 | 0.000 | 12.000 |
| Gemini 2.5 Pro | no_slip | 50.000 | 50.000 | 0.000 | 0.000 | 50.000 | 49.000 | 0.045 | 0.000 | 37.000 |
| Gemini 2.5 Pro | no_termination | 50.000 | 0.000 | 0.000 | 50.000 | 0.000 | 0.000 | NA | NA | 0.000 |

Case-best over available nonexternal successes：

| variant | cases | cases_with_variant_success | cases_with_any_external_failure | mean_casebest_delta_available_successes | median_casebest_delta_available_successes | reach_or_beat_full_plus_0p01_cases |
| --- | --- | --- | --- | --- | --- | --- |
| no_forbid | 50.000 | 49.000 | 33.000 | 0.018 | 0.000 | 45.000 |
| no_slip | 50.000 | 50.000 | 12.000 | -0.025 | 0.000 | 47.000 |
| no_termination | 50.000 | 50.000 | 50.000 | -0.079 | 0.000 | 47.000 |

Interpretation: 当前 rep50 mechanism 不能作为“完整三后端机制消融”写进主文；可用于说明 OpenAI 完整、Claude/Gemini 部分结果趋势，但必须等待远程 recovery 补齐 Gemini/Claude 外部失败后再做正式表/图。



## P6 CMU20 GPT-5.4 Multiseed

本轮 seed43–46 已完整；结合既有 canonical seed42，得到 5-seed × 20-case 审计。seed47 未纳入。

- 5-seed Full attempts: 100/100 success.

- Per-case range mean/median/max: 0.321 / 0.100 / 2.743 eV.

- Cases within 0.01/0.05/0.10 eV across five seeds: 3/20, 8/20, 10/20.

- Canonical seed42 is >0.01 eV worse than best-of-five on 11/20 cases; mean seed42-minus-best is 0.106 eV.

Largest multiseed spreads：

| case_id | min_energy | max_energy | range_eV | canonical_minus_best_seed_eV |
| --- | --- | --- | --- | --- |
| 20 | -11.652 | -8.909 | 2.743 | 0.000 |
| 15 | -3.575 | -2.927 | 0.648 | 0.317 |
| 16 | -4.796 | -4.272 | 0.524 | 0.524 |
| 18 | -3.229 | -2.724 | 0.505 | 0.505 |
| 08 | -7.368 | -6.911 | 0.457 | 0.178 |


## OCD24 Random Baseline vs AdsMind Full

Random baseline 是 n=20 随机候选，不是 LLM；这里与 AdsMind Full case-best-of-4 比较。负值表示 random 更低能。

- Random success: 24/24.

- Mean/median random-minus-AdsMind: -0.221 / -0.062 eV.

- Random lower / tie(0.01 eV) / AdsMind lower: 16/4/4.

- Random total wall-clock: 27.4 h; median per case 0.3 h.

Random strongest cases：

| case_id | random_best_energy | adsmind_full_best_energy | adsmind_full_best_backend | random_minus_adsmind_full_best_eV | comparison |
| --- | --- | --- | --- | --- | --- |
| 008 | -7.490 | -4.347 | GPT-5.4 | -3.144 | random_lower |
| 016 | -13.870 | -12.999 | GPT-5.4 | -0.871 | random_lower |
| 003 | -12.460 | -11.670 | GPT-5.4 | -0.791 | random_lower |
| 014 | -5.920 | -5.223 | Gemini 2.5 Pro | -0.698 | random_lower |
| 022 | -3.761 | -3.385 | Gemini 2.5 Pro | -0.377 | random_lower |

AdsMind strongest cases：

| case_id | random_best_energy | adsmind_full_best_energy | adsmind_full_best_backend | random_minus_adsmind_full_best_eV | comparison |
| --- | --- | --- | --- | --- | --- |
| 004 | -10.112 | -11.384 | GPT-5.4 | 1.273 | adsmind_lower |
| 024 | -3.445 | -3.716 | GPT-5.4 | 0.271 | adsmind_lower |
| 019 | -3.342 | -3.504 | GPT-5.4 | 0.162 | adsmind_lower |
| 007 | -10.635 | -10.732 | Claude Sonnet 4.6 | 0.097 | adsmind_lower |
| 020 | -6.236 | -6.242 | GPT-5.4 | 0.006 | tie_0p01 |


## Bottom Line

- 本轮数据把 OCD24 Grok single-shot 的大部分外部失败修掉了，但还剩 case017 外部缺口；OCD24 4-backend single-shot 不能声称 96/96 完整。

- OCD24 closed-loop 相对 1-shot 的可靠性优势仍然强：Full 96/96，1-shot 82/95 scientific attempts，且 1-shot 还有 1 个外部缺口。

- rep50 mechanism 这批“文件完整但科学不完整”：有 95 个外部 API/billing/overload 失败，不能直接用于主文正式结论；必须等 recovery 补齐。

- P6 multiseed 支持“Full 不是一次运气”的防御性 SI 结论，但能量 range 在部分 case 较大，应作为 stochasticity audit，不建议放主图核心。

- OCD24 random baseline 很强：random 在 16/24 case 低于 AdsMind Full case-best。论文里不能把 random 写成弱基线；应强调 AdsMind 的闭环反馈、诊断和可靠性，而不是绝对压过随机广搜。
