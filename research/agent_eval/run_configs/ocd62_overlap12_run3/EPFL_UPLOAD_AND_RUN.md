# EPFL RUN3 Upload Notes

Scope: this is only the third reproducibility run for the 12 overlap cases in
`datasets/ocd62_overlap12/`.

## Upload

```bash
rsync -av \
  datasets/ocd62_overlap12/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/datasets/ocd62_overlap12/

rsync -av \
  research/agent_eval/configs/ocd62_overlap12_run3/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/agent_eval/configs/ocd62_overlap12_run3/

rsync -av \
  research/agent_eval/run_configs/ocd62_overlap12_run3/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/agent_eval/run_configs/ocd62_overlap12_run3/
```

## Run On LIACPC12

```bash
cd /data/zongmin/workspace/AdsMind
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export OPENAI_API_KEY_FILE=/path/to/openai.key
export ANTHROPIC_API_KEY_FILE=/path/to/anthropic.key
export OPENROUTER_API_KEY_PRIMARY_FILE=/path/to/openrouter-primary.key
export OPENROUTER_API_KEY_SECONDARY_FILE=/path/to/openrouter-secondary.key
tmux new -s ocd62-run3
research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.sh
```

Use the GPT and Claude API keys for those backends. Use the primary Gemini/Grok
API key first; the launcher switches to the secondary key only when the primary
transport fails with an auth/quota/payment/rate-limit style error.

## Monitor

```bash
cd /data/zongmin/workspace/AdsMind
.venv/bin/python research/agent_eval/run_configs/ocd62_overlap12_run3/check_ocd62_overlap12_run3.py
tail -f research/agent_eval/run_configs/ocd62_overlap12_run3/logs/*.log
```

Expected completed outputs:

```text
research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/gpt54_mace_mp0_small/
research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/claude_sonnet46_mace_mp0_small/
research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/gemini25pro_mace_mp0_small/
research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/grok4_mace_mp0_small/
```

## Pull Results Back

```bash
rsync -av \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/ \
  research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/
```

Then locally:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```
