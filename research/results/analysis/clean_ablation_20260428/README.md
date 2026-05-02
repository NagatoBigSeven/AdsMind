# Clean Ablation Package 2026-04-28

本目录是用于写稿和作图的清洗版数据包。外部服务失败的 raw attempt 不进入正式统计；自然失败保留为运行失败，不用能量差替代。能量差统一定义为 `E_variant - E_full`，正值表示 ablated/1-shot 结果能量更高、稳定性更差。

## Coverage

| Dataset | Matrix | Attempts | Successful | Natural failures | External failures |
|---|---:|---:|---:|---:|---:|
| CMU20 4-backend 5-variant | clean | 400 | 393 | 7 | 0 |
| OCD24 4-backend 5-variant | clean | 480 | 465 | 15 | 0 |
| OCD-GMAE rep50 Full vs 1-Shot | clean | 400 | 375 | 25 | 0 |

## Aggregate Success By Variant

### CMU20 4-backend 5-variant
| Variant | Attempts | Successful | Natural failures | Success rate |
|---|---:|---:|---:|---:|
| Full | 80 | 80 | 0 | 1.0 |
| w/o Slip | 80 | 80 | 0 | 1.0 |
| w/o Forbid | 80 | 80 | 0 | 1.0 |
| w/o Term | 80 | 80 | 0 | 1.0 |
| 1-Shot | 80 | 73 | 7 | 0.9125 |

### OCD24 4-backend 5-variant
| Variant | Attempts | Successful | Natural failures | Success rate |
|---|---:|---:|---:|---:|
| Full | 96 | 96 | 0 | 1.0 |
| w/o Slip | 96 | 96 | 0 | 1.0 |
| w/o Forbid | 96 | 96 | 0 | 1.0 |
| w/o Term | 96 | 95 | 1 | 0.9896 |
| 1-Shot | 96 | 82 | 14 | 0.8542 |

### OCD-GMAE rep50 Full vs 1-Shot
| Variant | Attempts | Successful | Natural failures | Success rate |
|---|---:|---:|---:|---:|
| Full | 200 | 197 | 3 | 0.985 |
| 1-Shot | 200 | 178 | 22 | 0.89 |

## Success-only Delta Summary

### CMU20 4-backend 5-variant
| Variant | Paired successes | Mean delta eV | Median delta eV | Full better >0.05 eV | Variant better >0.05 eV | Within +/-0.05 eV |
|---|---:|---:|---:|---:|---:|---:|
| w/o Slip | 80 | -0.008477 | 0.0 | 9 | 11 | 60 |
| w/o Forbid | 80 | -0.007232 | 0.0 | 6 | 10 | 64 |
| w/o Term | 80 | -0.035681 | 0.0 | 5 | 10 | 65 |
| 1-Shot | 73 | 0.216976 | 0.125332 | 41 | 2 | 30 |

### OCD24 4-backend 5-variant
| Variant | Paired successes | Mean delta eV | Median delta eV | Full better >0.05 eV | Variant better >0.05 eV | Within +/-0.05 eV |
|---|---:|---:|---:|---:|---:|---:|
| w/o Slip | 96 | 0.013203 | 0.0 | 14 | 11 | 71 |
| w/o Forbid | 96 | 0.015007 | 0.0 | 10 | 6 | 80 |
| w/o Term | 95 | -0.012586 | 0.0 | 7 | 7 | 81 |
| 1-Shot | 82 | 0.3048 | 0.03124 | 40 | 0 | 42 |

### OCD-GMAE rep50 Full vs 1-Shot
| Variant | Paired successes | Mean delta eV | Median delta eV | Full better >0.05 eV | Variant better >0.05 eV | Within +/-0.05 eV |
|---|---:|---:|---:|---:|---:|---:|
| 1-Shot | 178 | 0.36442 | 0.071932 | 97 | 7 | 74 |

## Files
- `cmu20_delta_summary_by_variant_success_only.csv`
- `cmu20_delta_summary_success_only.csv`
- `cmu20_delta_vs_full_success_only.csv`
- `cmu20_merged_qc.csv`
- `cmu20_summary_by_backend_variant.csv`
- `cmu20_summary_by_variant.csv`
- `invalid_or_external_candidate_records.csv`
- `non_valid_selected_records.csv`
- `ocd24_delta_summary_by_variant_success_only.csv`
- `ocd24_delta_summary_success_only.csv`
- `ocd24_delta_vs_full_success_only.csv`
- `ocd24_merged_qc.csv`
- `ocd24_summary_by_backend_variant.csv`
- `ocd24_summary_by_variant.csv`
- `rep50_delta_summary_success_only.csv`
- `rep50_delta_vs_full_success_only.csv`
- `rep50_full_merged_qc.csv`
- `rep50_full_summary_by_backend_variant.csv`
- `rep50_full_vs_1shot_delta_success_only.csv`
- `rep50_full_vs_1shot_delta_summary_by_backend.csv`
- `rep50_full_vs_1shot_delta_summary_by_variant.csv`
- `rep50_full_vs_1shot_merged_qc.csv`
- `rep50_full_vs_1shot_summary_by_backend_variant.csv`
- `rep50_full_vs_1shot_summary_by_variant.csv`
- `rep50_mechanism_merged_qc.csv`
- `rep50_mechanism_summary_by_backend_variant.csv`
