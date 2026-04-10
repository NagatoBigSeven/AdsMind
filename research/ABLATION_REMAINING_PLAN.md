# Grok-4 Ablation: Completion Note

## Final Status (2026-04-10)

| Variant | 01 | 02 | 09 | 14 | 19 | Status |
|---------|----|----|----|----|-----|--------|
| full | -3.632 | -4.766 | -1.974 | -3.617 | -4.045 | **5/5 DONE** |
| no_slip | -3.632 | -4.766 | -1.974 | -3.617 | -3.594 | **5/5 DONE** |
| no_forbid | -3.632 | -4.760 | -1.974 | -3.617 | -3.594 | **5/5 DONE** |
| no_termination | -3.632 | -4.766 | -1.974 | -3.617 | -4.027 | **5/5 DONE** |
| single_shot | -3.631 | -4.150 | -1.974 | -3.245 | -3.594 | **5/5 AVAILABLE** |

**Remaining: 0 runs**

## Completion Summary

Completed in order:

1. `no_forbid` for cases `01, 02, 09, 14, 19`
2. `no_termination` for cases `01, 02, 09, 14, 19`
3. full summary rebuild with one-shot fallback

Final rebuilt outputs:

- `research/results/xai_ablation_v2/ablation_summary.csv`
- `research/results/xai_ablation_v2/ablation_stats.json`

All ten new `result.json` files exist and report `"status": "success"`.

## Commands to Execute

### Step 1: Set API key

```bash
export XAI_API_KEY="<your-xai-api-key>"
```

### Step 2: Run no_forbid (5 cases)

```bash
python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_xai_grok4.json \
  --output research/results/xai_ablation_v2 \
  --cases 01,02,09,14,19 \
  --variants no_forbid
```

### Step 3: Run no_termination (5 cases)

```bash
python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_xai_grok4.json \
  --output research/results/xai_ablation_v2 \
  --cases 01,02,09,14,19 \
  --variants no_termination
```

### Step 4: Rebuild full summary (after both complete)

```bash
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/xai_ablation_v2 \
  --one-shot-dir research/results/cmu_v1_xai_progressive_one_shot \
  --cases 01,02,09,14,19 \
  --variants full,no_slip,no_forbid,no_termination,single_shot
```

## Expected Runtime

- ~2-10 minutes per case, ~25 min average observed from no_slip batch
- 10 runs total: estimated **2-4 hours**
- Steps 2 and 3 can run sequentially in one terminal session

## What Was Checked After Completion

1. All 10 result.json files exist:
```bash
for v in no_forbid no_termination; do
  for c in 01 02 09 14 19; do
    f="research/results/xai_ablation_v2/$v/$c/result.json"
    if [ -f "$f" ]; then echo "OK   $v/$c"; else echo "MISS $v/$c"; fi
  done
done
```

2. All runs report `"status": "success"`
3. Case `19` remains the sensitive system:
   - `no_slip` and `no_forbid` degrade by about `+0.451 eV` vs `full`
   - `no_termination` nearly matches `full` (`+0.017 eV`) but spends more tokens
   - one `no_termination/19` attempt found a more stable dissociated state (`-4.379 eV`), but the runtime kept the best non-dissociated reference (`-4.027 eV`)

## Context for Codex

- The frozen config uses xAI's OpenAI-compatible endpoint with `grok-4-0709`
- `llm_api_key_env_var` in the config resolves the key from `$XAI_API_KEY`
- MACE calculator runs on CPU (macOS M3 Pro)
- `run_ablation.py` will overwrite `ablation_summary.csv` with only the current batch — that's fine, Step 4 rebuilds the full summary
- Do NOT rerun `full` or `no_slip` variants — they are already complete
- Do NOT pass `--api-key` flag — the env var mechanism handles it

## Collected Data Summary

| Dataset | Location | Cases | Status |
|---------|----------|-------|--------|
| Gemini 5×5 ablation | `gemini_ablation_v1/` | 5×5=25 | Complete |
| Grok-4 ablation | `xai_ablation_v2/` | 20/20 | Complete |
| Gemini 20-case one-shot | `cmu_v1_gemini_one_shot/` | 20/20 | Complete |
| Grok-4 20-case one-shot | `cmu_v1_xai_progressive_one_shot/` | 20/20 | Complete |
| Cross-LLM comparison | `cross_llm_ablation_comparison.csv` | 25 rows | Complete |
| Behavioral comparison | `adsmind_vs_adsorbagent_behavioral.csv` | 20 cases | Complete |
| Paper LaTeX tables | `paper_tables.tex` | - | Draft status unknown in current worktree |

## Key Findings So Far

1. **Cross-LLM convergence remains strong**: the Grok-4 full matrix is now complete and continues to support the earlier observation that iterative search reduces backend variance.
2. **Slip handling matters selectively**: case `19` is the clearest Grok-only failure mode. `no_slip` and `no_forbid` both degrade by about `+0.451 eV` relative to `full`.
3. **Termination is mostly a cost-control mechanism here**: `no_termination` matches `full` on `01`, `02`, `09`, and `14`, and is only `+0.017 eV` worse on `19`, but it consumes substantially more tokens on several cases.
4. **Single-shot remains the clearest baseline weakness**: compared with `full`, Grok-4 one-shot is worse by about `+0.615 eV` on `02`, `+0.372 eV` on `14`, and `+0.451 eV` on `19`.
