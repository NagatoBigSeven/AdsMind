# Codex Supplementary Ablation Execution Plan

## Overview

Six supplementary experiments to bring the ablation study from 75/100 to publication-ready.
All experiments run on the EPFL LIAC workstation (Ubuntu 22.04, RTX A6000, 48 GB VRAM).
AdsMind repo at `/data/zongmin/workspace/AdsMind`. CatalystAIgent at `/data/zongmin/CatalystAIgent`.

## API Keys

```bash
export OPENAI_API_KEY="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"
export XAI_API_KEY="xai-MXKM57ULNbP8lnkaRvDpOiJOEPRS7taBhscs2VjpaJRuXS5mFqnDqBepcsD35GwY2QSCNfV9oLTH9aT7"
export ANTHROPIC_API_KEY="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"
export GOOGLE_APPLICATION_CREDENTIALS=/data/zongmin/.config/gcloud/application_default_credentials.json
export GOOGLE_CLOUD_PROJECT=igneous-sandbox-479916-t9
```

Conda env: `llm_adsorbate` (for AdsMind), `adsorbagent` (for CatalystAIgent).

---

## Experiment 1: Random Placement Baseline (CRITICAL)

### Purpose

Prove that the LLM planner adds value over random guessing. Without this, a reviewer can claim the improvement is entirely from the MACE relaxation pipeline, not the LLM.

### Design

For each of the 15 CMU cases, generate N random adsorbate placements on the surface, relax each with the same MACE protocol, and take the best energy. Compare against AdsMind Full and 1-Shot variants.

### Implementation

Create a new script `research/agent_eval/run_random_baseline.py` that:

1. Loads the slab from `benchmark_slabs/{case_id}_*.xyz`
2. Loads the adsorbate SMILES from `manifests/cmu_manifest.csv`
3. For each case, generates N=20 random placements:
   - Pick a random (x, y) position within the slab's periodic cell
   - Place adsorbate z at surface_z_max + 2.0 Å
   - Random rotation (Euler angles uniformly sampled)
   - Apply same FixAtoms constraint (bottom 1/3 slab)
4. Relaxes each with MACE-MP-0 small (cpu, float32, fmax=0.10, steps=200)
5. Records best energy across N placements

N=20 matches AdsMind's ~4 iterations × ~5 conformers evaluated (though only 1 relaxed), so it's compute-matched to Adsorb-Agent's median.

```python
import numpy as np
from ase.io import read
from ase.optimize import BFGS
from ase.constraints import FixAtoms
from mace.calculators import mace_mp
from ase.build import add_adsorbate
from scipy.spatial.transform import Rotation

FIXED_BOTTOM_FRACTION = 1.0 / 3.0
N_RANDOM = 20

def random_placement_baseline(slab_path, adsorbate_atoms, seed=42):
    """Generate N random placements, relax each, return best energy."""
    np.random.seed(seed)
    slab = read(slab_path)
    calc = mace_mp(model="small", device="cpu", default_dtype="float32")

    # Surface z
    z_max = slab.positions[:, 2].max()

    # Constraint
    tags = slab.get_tags() if any(slab.get_tags()) else np.zeros(len(slab), dtype=int)
    slab_z = slab.positions[:, 2]
    z_thresh = slab_z.min() + (slab_z.max() - slab_z.min()) * FIXED_BOTTOM_FRACTION

    results = []
    for i in range(N_RANDOM):
        # Random position within cell
        frac = np.random.rand(2)
        xy = frac @ slab.cell[:2, :2]
        z = z_max + 2.0  # 2 Å above surface

        # Random rotation
        rot = Rotation.random()
        ads = adsorbate_atoms.copy()
        ads.positions = rot.apply(ads.positions - ads.get_center_of_mass())
        ads.positions += [xy[0], xy[1], z]

        # Combine
        system = slab + ads
        system.set_constraint(FixAtoms(indices=[
            j for j in range(len(slab))
            if slab.positions[j, 2] < z_thresh
        ]))
        system.calc = calc

        try:
            opt = BFGS(system, logfile=None)
            opt.run(fmax=0.10, steps=200)
            e = system.get_potential_energy()
            results.append(e)
        except:
            pass

    return min(results) if results else None
```

### Execution

```bash
tmux new-session -d -s random-baseline
source /data/zongmin/anaconda3/bin/activate llm_adsorbate
cd /data/zongmin/workspace/AdsMind
python -u -m research.agent_eval.run_random_baseline \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
  --n-random 20 \
  --output research/results/random_baseline_n20 \
  2>&1 | tee /tmp/random_baseline.log
```

Estimated time: 15 cases × 20 relaxations × ~30s = ~2.5 hours.

### Output

`research/results/random_baseline_n20/summary.csv` with columns: case_id, n_random, best_energy, mean_energy, std_energy.

### Verification

- All 15 cases should produce results (random placement can't fail like LLM site selection)
- Random baseline energy should be worse than both AdsMind Full and 1-Shot in most cases
- If random beats LLM on many cases → the LLM planner needs improvement (important finding either way)

---

## Experiment 2: Iteration-Count Sensitivity Curve (CRITICAL)

### Purpose

Show how AdsMind's best energy improves with each iteration. This demonstrates the value of closed-loop refinement and the convergence rate of the search.

### Design

No new experiments needed — extract per-iteration best energy from existing `result.json` files. The `attempt_records` array contains `most_stable_energy_eV` for each iteration.

### Implementation

Create `research/agent_eval/iteration_convergence.py`:

```python
import json, csv
from pathlib import Path
import numpy as np

def extract_convergence(result_json_path):
    """Extract running-best energy at each iteration."""
    with open(result_json_path) as f:
        data = json.load(f)
    records = data.get("attempt_records", [])
    running_best = []
    best_so_far = float("inf")
    for rec in records:
        e = rec.get("most_stable_energy_eV")
        if e is not None and rec.get("status") == "success":
            best_so_far = min(best_so_far, e)
        running_best.append(best_so_far if best_so_far != float("inf") else None)
    return running_best
```

Process all 4 backends × 15 CMU cases × full variant. Output a table:

```
case_id, backend, iter_1, iter_2, iter_3, iter_4, iter_5, final_best
```

### Execution

This is pure post-processing — no API calls, no MACE. Runs in seconds.

```bash
python -u -m research.agent_eval.iteration_convergence \
  --ablation-dirs research/results/gemini_ablation_v1,research/results/xai_ablation_v2,research/results/openai_gpt54_ablation_v1,research/results/anthropic_sonnet46_ablation_v1 \
  --variant full \
  --output research/results/analysis/iteration_convergence.csv
```

### Analysis

- Plot: best energy vs iteration number (averaged across cases, per backend)
- Key metric: what fraction of the full-run improvement is achieved by iteration 2? by iteration 3?
- Expected: steep drop at iteration 1→2 (first slip correction), then diminishing returns

---

## Experiment 3: Adsorb-Agent Multi-Backend (RECOMMENDED)

### Purpose

Currently Adsorb-Agent was only run with GPT-4o. Running it with GPT-5.4 enables a same-LLM comparison (GPT-5.4 AdsMind vs GPT-5.4 Adsorb-Agent), eliminating LLM capability as a confound.

### Design

Run the modified CatalystAIgent (MACE backend, FixAtoms constraints) with GPT-5.4 on the same 20 CMU cases. The code is already set up from the previous run — just change the config.

### Implementation

Create `config/adsorb_agent_cmu_gpt54.yaml`:

```yaml
agent_settings:
  provider: "openai"
  version: "gpt-5.4-2026-03-05"
  gnn_model: "mace-mp-0-small"
  mode: "llm-guided"
  critic_activate: true
  random_ratio: 0.2
  init_multiplier: 1.0

paths:
  question_path: "/data/zongmin/CatalystAIgent/reasoning/reasoning.txt"
  knowledge_path: "/data/zongmin/CatalystAIgent/reasoning/knowledge.txt"
  metadata_path: null
  bulk_db_path: "/data/zongmin/CatalystAIgent/fairchem-forked/src/fairchem/data/oc/databases/pkls/bulks.pkl"
  ads_db_path: "/data/zongmin/CatalystAIgent/fairchem-forked/src/fairchem/data/oc/databases/pkls/adsorbates.pkl"
  save_dir: "/data/zongmin/CatalystAIgent/results/cmu_benchmark_gpt54"
  system_dir: "/data/zongmin/CatalystAIgent/config/cmu_benchmark"
```

### Execution

```bash
tmux new-session -d -s aa-gpt54
source /data/zongmin/anaconda3/bin/activate adsorbagent
cd /data/zongmin/CatalystAIgent
python -u adsorb_agent.py --path config/adsorb_agent_cmu_gpt54.yaml \
  2>&1 | tee /tmp/aa_gpt54.log
```

Estimated time: ~2-4 hours (20 cases, same as GPT-4o run).

### Analysis

Compare GPT-5.4 Adsorb-Agent vs GPT-5.4 AdsMind (from `openai_gpt54_ablation_v1/full`):
- Same LLM, same physics, different architecture → isolates search strategy effect
- Also compare GPT-5.4 AA success rate vs GPT-4o AA success rate → measures LLM capability impact on Adsorb-Agent

---

## Experiment 4: High-Symmetry Site Heuristic Baseline (RECOMMENDED)

### Purpose

A stronger non-LLM baseline than random. Places adsorbate at every canonical high-symmetry site (ontop, bridge, hollow) and relaxes each. This represents a "textbook computational chemistry" approach.

### Design

For each of the 15 CMU cases:
1. Use AutoAdsorbate (already in AdsMind) to enumerate ALL adsorption sites on the surface
2. For each site, place the adsorbate in a default orientation
3. Relax each with MACE (same protocol)
4. Take the best energy across all sites

This is essentially "Adsorb-Agent without the LLM" — enumerate sites algorithmically, skip the LLM reasoning step entirely.

### Implementation

Create `research/agent_eval/run_heuristic_baseline.py`:

```python
from autoadsorbate import Surface
from src.tools.patches import get_shrinkwrap_ads_sites_fixed

def heuristic_baseline(slab_path, adsorbate_smiles):
    """Enumerate all high-symmetry sites, place + relax at each."""
    slab = read(slab_path)
    # Use autoadsorbate to find all sites
    surface = Surface(slab, precision=1.0, touch_sphere_size=2.0, mode="slab")
    sites = surface.site_df

    # For each site, create fragment + relax
    # (reuse AdsMind's fragment.py placement logic but skip LLM)
    ...
```

This reuses AdsMind's existing `autoadsorbate` integration but bypasses the LLM planner entirely.

### Execution

```bash
tmux new-session -d -s heuristic-baseline
source /data/zongmin/anaconda3/bin/activate llm_adsorbate
cd /data/zongmin/workspace/AdsMind
python -u -m research.agent_eval.run_heuristic_baseline \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
  --output research/results/heuristic_baseline \
  2>&1 | tee /tmp/heuristic_baseline.log
```

Estimated time: 15 cases × ~30-50 sites × ~30s = ~4-7 hours.

### Analysis

- Compare against: Random baseline (weaker), AdsMind 1-Shot (LLM single-pass), AdsMind Full (LLM closed-loop), Adsorb-Agent (LLM multi-config)
- Expected ranking: Random < Heuristic ≤ 1-Shot < Full
- If Heuristic ≥ Full on many cases → the LLM planner is not adding value beyond systematic enumeration

---

## Experiment 5: DFT Validation (P0 — requires Bowen)

### Purpose

Validate that MACE energy rankings are consistent with DFT. This is the single most important experiment for scientific credibility.

### Design

For each of 5 representative cases (spanning simple→complex):
- Take the 3 best structures from: AdsMind Full, Adsorb-Agent, Random baseline
- Run DFT single-point energy on each (9 structures per case = 45 total)
- Check whether the MACE-based ranking holds under DFT

### Case Selection

| Case | Surface | Adsorbate | Why |
|------|---------|-----------|-----|
| 05 | Cu3Ag(111) | H | Simplest, near-tie between AM/AA (Δ=0.008 eV) |
| 14 | CoPt(111) | OH | Intermetallic, medium complexity |
| 16 | Au2Hf(102) | CH2CH2OH | Largest AM/AA gap (2.04 eV), complex adsorbate |
| 18 | Al3Zr(101) | OCHCH3 | Second largest gap (1.35 eV) |
| 20 | Bi2Ti6(211) | ONN(CH3)2 | AA failed, AM succeeded — tests edge case |

### Implementation

**This experiment requires Bowen (DFT expertise) and Prof. Cheng's cluster.** Codex prepares the input structures; Bowen runs VASP/QE.

Codex should:
1. Extract the best relaxed structures from AdsMind, Adsorb-Agent, and Random baseline for each case
2. Write them as POSCAR/CIF files in `research/dft_validation/inputs/`
3. Generate template VASP INCAR/KPOINTS files with appropriate settings for each surface

```bash
python -u -m research.agent_eval.prepare_dft_validation \
  --cases 05,14,16,18,20 \
  --adsmind-dir research/results/openai_gpt54_ablation_v1/full \
  --adsorbagent-dir research/results/adsorbagent_mace_gpt4o \
  --random-dir research/results/random_baseline_n20 \
  --output research/dft_validation/inputs
```

### Analysis

- Spearman rank correlation between MACE energies and DFT energies
- Key question: does the MACE ordering (AA < AM for cases 16, 18) hold under DFT?
- If correlation > 0.8, MACE rankings are reliable and all conclusions hold

---

## Experiment 6: MACE Model Size Sensitivity (NICE TO HAVE)

### Purpose

All experiments use MACE-small (CPU, float32). Show that conclusions are robust to the force field fidelity by repeating a subset of runs with MACE-large (GPU, float64, dispersion).

### Design

Run AdsMind Full variant on 5 representative cases with MACE-large on GPU. Compare energy rankings (not absolute values) with MACE-small results.

### Implementation

Create a new frozen config `frozen_config_openai_gpt54_mace_large.json`:

```json
{
  "llm_backend": "openrouter",
  "llm_model": "gpt-5.4-2026-03-05",
  "llm_base_url": "https://api.openai.com/v1",
  "llm_api_key_env_var": "OPENAI_API_KEY",
  "temperature": 0.0,
  "max_tokens": 4096,
  "timeout_sec": 120,
  "max_retries": 5,
  "relaxation_mode": "standard",
  "calculator_backend": "mace",
  "mace_device": "cuda",
  "mace_precision": "float64",
  "mace_model": "large",
  "mace_use_dispersion": true,
  "fmax": 0.05,
  "random_seed": 42,
  "platform": "EPFL-RTX-A6000-float64",
  "notes": ["MACE-large GPU validation run"]
}
```

### Execution

```bash
tmux new-session -d -s mace-large
source /data/zongmin/anaconda3/bin/activate llm_adsorbate
cd /data/zongmin/workspace/AdsMind
python -u -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_openai_gpt54_mace_large.json \
  --output research/results/mace_large_gpt54 \
  --cases 05,14,16,18,20 \
  --variants full \
  2>&1 | tee /tmp/mace_large.log
```

Estimated time: 5 cases × ~10 min = ~50 min (GPU relaxation is much faster).

### Analysis

- Compare energy RANKINGS (not absolute values) between MACE-small and MACE-large
- Spearman correlation of per-case energies
- If rankings are preserved, all MACE-small conclusions are robust

---

## Execution Priority and Parallelism

```
Timeline (all in tmux sessions):

Hour 0-1:    Exp 2 (iteration convergence) — pure post-processing, instant
             Exp 1 (random baseline) — start immediately, ~2.5h
             Exp 3 (AA GPT-5.4) — start immediately, ~3h

Hour 1-3:    Exp 4 (heuristic baseline) — start after Exp 2 done, ~5h
             Exp 6 (MACE-large) — start immediately (GPU), ~1h

Hour 3+:     Exp 5 (DFT prep) — prepare input structures after Exp 1 finishes
             All results available by hour ~6
```

Experiments 1, 3, 6 can run in parallel (different tmux sessions, different resources).
Experiment 2 is instant.
Experiment 4 runs after 2 (reuses code).
Experiment 5 only prepares inputs; DFT runs are Bowen's responsibility.

## Commit and Push

After ALL experiments complete:

```bash
cd /data/zongmin/workspace/AdsMind
git add -A
git commit -m "data: supplementary ablation experiments (random baseline, iteration convergence, AA multi-backend, heuristic baseline, MACE-large sensitivity)

- Random placement baseline (N=20): establishes non-LLM lower bound
- Iteration convergence curves: extracted from existing data
- Adsorb-Agent GPT-5.4: same-LLM comparison with AdsMind
- High-symmetry heuristic baseline: textbook approach comparison
- MACE-large GPU sensitivity: validates ranking robustness
- DFT validation inputs prepared for 5 representative cases

Co-Authored-By: Codex <noreply@openai.com>"

git push origin main
```
