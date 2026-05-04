# EPFL RUN3 Upload Notes

Scope: this is only the third reproducibility run for the 12 overlap cases in
`datasets/ocd62_overlap12/`.

## Upload

```bash
rsync -av \
  datasets/ocd62_overlap12/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/datasets/ocd62_overlap12/

rsync -av \
  research/agent_eval/configs/ocd62_overlap12_run3_native/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/agent_eval/configs/ocd62_overlap12_run3_native/

rsync -av \
  research/agent_eval/configs/ocd62_overlap12_run3_openrouter/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/agent_eval/configs/ocd62_overlap12_run3_openrouter/

rsync -av \
  research/agent_eval/run_configs/ocd62_overlap12_run3/ \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/agent_eval/run_configs/ocd62_overlap12_run3/
```

## Run On LIACPC12

```bash
cd /data/zongmin/workspace/AdsMind
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
tmux new -s ocd62-run3
research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.sh
```

## Monitor

```bash
cd /data/zongmin/workspace/AdsMind
.venv/bin/python research/agent_eval/run_configs/ocd62_overlap12_run3/check_ocd62_overlap12_run3.py
tail -f research/agent_eval/run_configs/ocd62_overlap12_run3/logs/*.log
```

Expected completed outputs:

```text
research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/gpt/
research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/claude/
research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/gemini/
research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/grok/
```

## Pull Results Back

```bash
rsync -av \
  LIACPC12:/data/zongmin/workspace/AdsMind/research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/ \
  research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/
```

Then locally:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```
