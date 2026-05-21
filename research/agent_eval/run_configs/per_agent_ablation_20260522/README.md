# Per-agent ablation (no_executor + no_validator)

Date: 2026-05-22

Tests Lixue's concern that the LLM may already encode enough chemistry that
the executor (MACE-MP-0 small) and validator are not pulling their weight.

## Variants added

- `no_executor`: planner outputs a `predicted_relaxed_energy_eV` field; the
  MACE relaxation is bypassed and the LLM-predicted energy stands in. All
  other modules (validator, slip / forbid / termination feedback) stay on.
- `no_validator`: the Python schema validator becomes a minimal
  pass-through. Planner errors propagate straight to the executor.

Both run with `max_attempts=5` and `random_seed=42`, matching `full`. Single
variable changes per row.

## Scope

- Dataset: `datasets/cmu20/cmu20_manifest.csv` (20 cases)
- Backends: 4 (gpt54, claude_sonnet46, gemini25pro, grok4)
- Variants: `no_executor`, `no_validator`
- Total runs: 20 cases × 4 backends × 2 variants = 160

Case order is `01,02,03,04,09,10` first (Bowen DFT subset) then the
remaining 14, so the morning audit can read DFT comparisons earliest.

## Run on LIACPC12

```bash
cd /data/zongmin/workspace/AdsMind
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export OPENROUTER_API_KEY=...
tmux new -s per-agent-ablation
research/agent_eval/run_configs/per_agent_ablation_20260522/run_per_agent_ablation.sh
```

## Outputs

```
research/results/basic_experiments/cmu20/adsmind/<backend_dir>/
  no_executor/<case_id>/result.json
  no_validator/<case_id>/result.json
research/results/run_logs/per_agent_ablation_<timestamp>/
  master.log
  gpt.log
  claude.log
  gemini.log
  grok.log
```

## Scientific reading

- LLM-predicted vs MACE-relaxed (per case) → does the LLM already know what
  MACE would say?
- LLM-predicted vs DFT (cases 01,02,03,04,09,10) → does the LLM already
  know what DFT would say?
- no_validator vs full → does the validator catch real planner errors, or
  is it just guarding against a hallucination rate of zero?
