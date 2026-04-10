# Claude Sonnet 4.6 EPFL Runbook

Purpose: run the same AdsMind agent-side protocol used for Gemini, Grok-4, and GPT-5.4 with Claude Sonnet 4.6 on the EPFL workstation.

This runbook uses Anthropic's OpenAI-compatible Chat Completions endpoint so the existing AdsMind `openrouter` transport can be reused with only `base_url`, model, and API-key changes.

## Scope

Run these datasets:

- 20-case one-shot baseline: `research/results/cmu_v1_anthropic_sonnet46_one_shot`
- 5 x 5 ablation matrix: `research/results/anthropic_sonnet46_ablation_v1`

Locked protocol:

- Model: `claude-sonnet-4-6`
- API key environment variable: `ANTHROPIC_API_KEY`
- LLM temperature: `0.0`
- Max output tokens: `4096`
- MACE: `small`, `cpu`, `float32`, no dispersion
- Relaxation: standard, `fmax=0.10`
- Manifest: `research/agent_eval/manifests/cmu_manifest.csv`

## 1. Clone And Install

```bash
git clone https://github.com/AI4QC/AdsMind.git
cd AdsMind
git checkout main
git pull --ff-only origin main
```

Install with `uv`:

```bash
uv sync --extra dev --extra research
uv run adsmind-preflight
```

If `uv` is not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
exec "$SHELL" -l
uv sync --extra dev --extra research
```

## 2. Export The Anthropic API Key Safely

Do not paste the key into a command line. Use a silent prompt so the key does not enter shell history:

```bash
read -rsp "ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY
echo
```

Confirm it is present without printing it:

```bash
python - <<'PY'
import os
key = os.environ.get("ANTHROPIC_API_KEY", "")
print("ANTHROPIC_API_KEY loaded:", bool(key), "length:", len(key))
PY
```

## 3. Verify Anthropic Access

List models and confirm Sonnet 4.6 is visible:

```bash
python - <<'PY'
import os
import requests

headers = {
    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
    "anthropic-version": "2023-06-01",
}
resp = requests.get("https://api.anthropic.com/v1/models", headers=headers, timeout=30)
print("status:", resp.status_code)
resp.raise_for_status()
models = resp.json().get("data", [])
for model in models:
    model_id = model.get("id", "")
    display = model.get("display_name", "")
    if "sonnet" in model_id.lower() or "sonnet" in display.lower():
        print(model_id, "|", display)
PY
```

Smoke-test Anthropic's OpenAI-compatible endpoint:

```bash
python - <<'PY'
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    base_url="https://api.anthropic.com/v1/",
)
resp = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Reply with exactly: ok"}],
    temperature=0,
    max_tokens=8,
)
print(resp.choices[0].message.content)
print("usage:", resp.usage)
PY
```

If this fails with `model_not_found`, replace `claude-sonnet-4-6` in both Claude config files with the exact model id printed by the model-list command.

## 4. Cheap Local Dry Run

This checks the runner layer without spending Anthropic tokens:

```bash
uv run python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46_one_shot.json \
  --output research/results/cmu_v1_anthropic_sonnet46_dryrun \
  --case-ids 09 \
  --dry-run

uv run python -m research.agent_eval.summarize_runs \
  --output research/results/cmu_v1_anthropic_sonnet46_dryrun
```

Expected: `research/results/cmu_v1_anthropic_sonnet46_dryrun/09/result.json` exists and `summary.csv` parses.

## 5. Real Smoke Case

Run case 09 first because it is cheap and historically stable:

```bash
uv run python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46_one_shot.json \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot \
  --case-ids 09

uv run python -m research.agent_eval.summarize_runs \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot
```

Check the smoke result:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("research/results/cmu_v1_anthropic_sonnet46_one_shot/09/result.json")
data = json.loads(path.read_text())
print("status:", data.get("status"))
print("energy:", data.get("best_energy_eV"))
print("iterations:", data.get("iteration_count"))
print("tokens:", data.get("total_input_tokens", 0) + data.get("total_output_tokens", 0))
print("dissociation_count:", data.get("dissociation_count"))
print("chemical_slip_count:", data.get("chemical_slip_count"))
PY
```

Proceed only if `status` is `success`, token count is non-zero, and there is no unexpected API/runtime error.

## 6. Full 20-Case One-Shot Baseline

Run inside `tmux` or `screen` so SSH disconnects do not kill the job:

```bash
tmux new -s adsmind-sonnet46
```

Inside the session, export `ANTHROPIC_API_KEY` again using the silent prompt from step 2, then run:

```bash
uv run python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46_one_shot.json \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot \
  --skip-existing

uv run python -m research.agent_eval.summarize_runs \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot
```

Detach from tmux with `Ctrl-b d`; reattach with:

```bash
tmux attach -t adsmind-sonnet46
```

## 7. Ablation Matrix

Run the locked 5-case x 5-variant matrix:

```bash
uv run python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46.json \
  --output research/results/anthropic_sonnet46_ablation_v1 \
  --cases 01,02,09,14,19
```

If the run is interrupted, resume by running only missing variants:

```bash
uv run python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46.json \
  --output research/results/anthropic_sonnet46_ablation_v1 \
  --cases 01,02,09,14,19 \
  --variants full
```

Replace `full` with any missing variant from:

```text
full,no_slip,no_forbid,no_termination,single_shot
```

## 8. Quality Checks Before Commit

Run:

```bash
uv run --extra dev pytest

python - <<'PY'
import csv
import json
from pathlib import Path

one = Path("research/results/cmu_v1_anthropic_sonnet46_one_shot")
abl = Path("research/results/anthropic_sonnet46_ablation_v1")

one_results = sorted(one.glob("*/result.json"))
abl_results = sorted(abl.glob("*/*/result.json"))
print("one-shot result.json:", len(one_results))
print("ablation result.json:", len(abl_results))

for path in one_results + abl_results:
    json.loads(path.read_text())

with (one / "summary.csv").open() as f:
    one_rows = list(csv.DictReader(f))
print("one-shot summary rows:", len(one_rows))

with (abl / "ablation_summary.csv").open() as f:
    abl_rows = list(csv.DictReader(f))
print("ablation summary rows:", len(abl_rows))
print("ablation successes:", sum(row["success"] == "True" for row in abl_rows))
PY
```

Expected complete counts:

- One-shot: 20 `result.json`, 20 summary rows.
- Ablation: 25 `result.json`, 25 summary rows.

## 9. Package And Push From EPFL

Do not commit raw tarballs, API keys, or shell history. Commit result JSON/CSV summaries only:

```bash
git status --short
git add \
  research/results/cmu_v1_anthropic_sonnet46_one_shot \
  research/results/anthropic_sonnet46_ablation_v1

git diff --cached --name-only | grep -E 'agent_log|config.json|artifacts|\\.traj$|\\.xyz$|\\.tar\\.gz$' && echo "Unexpected staged artifact" && exit 1 || true
git diff --cached --no-ext-diff | grep -E 'API_KEY[[:space:]]*=' && echo "Secret-like env assignment detected" && exit 1 || true

git commit -m "data: add claude sonnet 4.6 benchmark evidence"
git push origin HEAD:claude-sonnet46
```

After pushing, send back:

- Branch name and commit hash.
- `summary.csv` from the one-shot run.
- `ablation_summary.csv` and `ablation_stats.json`.
- Any failed case ids and their `result.json`.

## 10. Interpretation Rules

- Do not claim Claude Sonnet 4.6 achieved 20/20 unless every one-shot `result.json` has `status=success`.
- If a case fails by dissociation, report it as a chemistry/agent outcome, not an API failure.
- Do not compare Claude energy against Adsorb-Agent paper energies as a same-quantity energy comparison; compare Claude against Gemini/Grok-4/GPT-5.4 under the same AdsMind+MACE protocol.
- Keep the model id and `source_commit` values from each `config.json` for provenance, but do not commit per-run `config.json` files if they contain environment metadata you do not want in Git.
