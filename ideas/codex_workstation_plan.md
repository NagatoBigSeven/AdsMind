# Codex Workstation Execution Plan

## Target: EPFL LIAC Workstation

- Host: `128.178.38.24`, User: `zongmin`, Password: `iniliac122511181553`
- Ubuntu 22.04, CUDA 12.1, RTX A6000 (48 GB VRAM), 24 cores, 61 GB RAM
- AdsMind repo already cloned on workstation (locate with `find /home/zongmin -name "AdsMind" -type d 2>/dev/null`)
- All work in tmux sessions for persistence

## API Keys

```bash
export XAI_API_KEY="xai-MXKM57ULNbP8lnkaRvDpOiJOEPRS7taBhscs2VjpaJRuXS5mFqnDqBepcsD35GwY2QSCNfV9oLTH9aT7"
export ANTHROPIC_API_KEY="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"
export OPENAI_API_KEY="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"
```

Google Vertex AI:

- API Key / Access Token: `AQ.Ab8RN6KbiYsOPCy-Q-EPb34t3SOv9yCLe7607F07OdBHU65u4Q`
- Google Account: `zzmhkust@gmail.com`
- Project ID: `igneous-sandbox-479916-t9`
- Docs: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start?hl=zh-cn>

---

## Task 1: Gemini OCD-GMAE Rerun (Direct API, No Proxy)

### Problem

The current Gemini OCD-GMAE data was collected through an AiHubMix proxy (`aihubmix.com/v1`), which introduced systematic artifacts:

1. **Premature termination** — Case 013: Full variant stopped after 1 iteration (3,768 tokens) at -9.078 eV, while ablated variants ran 5 iterations and found -10.2 eV (matching other backends). The proxy likely corrupted the termination signal.
2. **Systematic basin-missing** — Case 003: All ablated variants converge to -10.629 eV (1.0 eV worse than Full at -11.655), while all three direct-API backends find -11.655 across ALL variants. Case 004 shows similar pattern.

These artifacts do NOT appear in the CMU Gemini data (also via AiHubMix), suggesting the harder OCD-GMAE surfaces amplify proxy instability.

### Solution

Rerun all 50 Gemini OCD-GMAE runs using Google Vertex AI direct API (no proxy).

### Platform Note

All existing 500 runs (CMU + OCD-GMAE, all 4 backends) were collected on macOS M3 Pro (ARM). This rerun will be on Linux x86_64. With identical MACE config (cpu/small/float32/fmax=0.10), energy differences due to platform BLAS should be sub-meV — negligible at the 0.1-1.0 eV scale of our comparisons. However, this means the new Gemini data is on a different platform than the other 3 backends' OCD-GMAE data. This is acceptable because: (a) within-Gemini comparisons (full vs ablated) are self-consistent, and (b) the cross-LLM table previously excluded Gemini anyway.

### Old Data Disposition

Rename `ocd_gmae_gemini_ablation_v1/` to `ocd_gmae_gemini_ablation_v1_aihubmix_archived/` for reference. Do NOT delete — it documents the proxy artifact for the paper's methods section.

### Vertex AI Model Version Note

Vertex AI's Gemini 2.5 Pro may be a different checkpoint than AiHubMix's. This is expected and acceptable — the CMU Gemini data (AiHubMix) and new OCD-GMAE data (Vertex AI) serve different purposes. The CMU data is already clean and stays as-is.

### Steps

#### 1.1 Set up Vertex AI Gemini access

The provided credential (`AQ.Ab8R...`) may be an OAuth access token rather than a standard API key. Codex must determine the correct authentication method:

**Option A: google-genai SDK (preferred if it works)**

```bash
pip install google-genai
```

```python
from google import genai
client = genai.Client(
    vertexai=True,
    project="igneous-sandbox-479916-t9",
    location="us-central1"  # or europe-west1
)
# Test with: client.models.generate_content(model="gemini-2.5-pro", ...)
```

**Option B: LangChain ChatVertexAI**

```bash
pip install langchain-google-vertexai
```

Codex must authenticate with `gcloud auth login` or `gcloud auth application-default login` using `zzmhkust@gmail.com`, then test that Gemini 2.5 Pro is accessible. The provided token `AQ.Ab8R...` may need to be set as `GOOGLE_API_KEY` or used via `gcloud auth print-access-token`. Consult the Vertex AI docs link above.

#### 1.2 Create a new frozen config

Create `research/agent_eval/configs/frozen_config_gemini25pro_vertexai.json`:

```json
{
  "llm_backend": "google_vertexai",
  "llm_model": "gemini-2.5-pro",
  "llm_api_key_env_var": "GOOGLE_API_KEY",
  "temperature": 0.0,
  "max_tokens": 4096,
  "timeout_sec": 120,
  "max_retries": 5,
  "relaxation_mode": "standard",
  "calculator_backend": "mace",
  "mace_device": "cpu",
  "mace_precision": "float32",
  "mace_model": "small",
  "mace_use_dispersion": false,
  "fmax": 0.10,
  "random_seed": 42,
  "platform": "Ubuntu-22.04-x86_64-float32",
  "transport_variant": "vertex-ai-direct",
  "notes": ["Direct Vertex AI access, replacing AiHubMix proxy to eliminate proxy artifacts."]
}
```

CRITICAL: `mace_device`, `mace_model`, `mace_precision`, `fmax` MUST match the original config exactly (cpu, small, float32, 0.10). The ONLY change is the LLM transport layer. We explicitly use float32 even though Linux CPU defaults to float64 — this is intentional to stay consistent with the macOS-collected data.

If the AdsMind codebase does not already support a `google_vertexai` backend, Codex must add it. Check `src/llm/` or wherever the LLM client is instantiated. The change should be minimal: add a `ChatVertexAI` or `google-genai` client path alongside the existing `openrouter` path.

#### 1.3 Create OCD-GMAE manifest

The 10 OCD-GMAE cases are: 003, 004, 005, 012, 013, 015, 016, 019, 023, 024. The manifest should already exist at `research/agent_eval/manifests/ocd_gmae_manifest.csv`. If not, create it from the existing OCD-GMAE data.

#### 1.4 Run the ablation matrix

```bash
tmux new-session -d -s gemini-rerun

# Inside tmux:
# 50 runs total: 10 cases x 5 variants (full, no_slip, no_forbid, no_termination, single_shot)
python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/ocd_gmae_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai.json \
  --output research/results/ocd_gmae_gemini_ablation_v2 \
  --cases 003,004,005,012,013,015,016,019,023,024 \
  --variants full,no_slip,no_forbid,no_termination,single_shot
```

#### 1.5 Rebuild summary and verify

```bash
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/ocd_gmae_gemini_ablation_v2 \
  --one-shot-dir research/results/ocd_gmae_gemini_ablation_v2/single_shot \
  --cases 003,004,005,012,013,015,016,019,023,024 \
  --variants full,no_slip,no_forbid,no_termination,single_shot
```

Verification checklist:

- [ ] 50/50 runs succeeded
- [ ] Case 013 Full runs 3+ iterations (not 1)
- [ ] Case 003 ablated variants find energies near -11.655 (not -10.629)
- [ ] Case 004 ablated variants find energies near -10.1 to -11.4 (not -9.2 to -9.7)

---

## Task 2: Adsorb-Agent Comparison Under MACE (Route A)

### Goal

Fork CatalystAIgent, replace its EquiformerV2 relaxation backend with MACE-MP-0 (matching AdsMind's exact physical backend), then run it on the 20 CMU benchmark cases. This produces an apples-to-apples comparison of search strategies under identical physics.

### Case Scope

Adsorb-Agent paper defines 20 cases (01-20). AdsMind's ablation benchmark uses 15 of these (01-02, 04-05, 09-10, 12-20). Cases 03, 06, 07, 08, 11 are NOT in AdsMind's ablation set.

**Run all 20 cases.** The 15 overlapping cases allow direct energy comparison with AdsMind. The 5 extra cases provide additional Adsorb-Agent-under-MACE data points (no AdsMind comparison, but useful for characterizing Adsorb-Agent's behavior).

### Adsorb-Agent Architecture (from source analysis)

CatalystAIgent is a single-pass LLM planner:

1. **Reasoning** — LLM rephrases domain knowledge prompts
2. **Solution** — LLM proposes adsorption site type, binding atoms, orientation
3. **Critic** — LLM validates site-type/orientation consistency (loop until valid)
4. **Structure generation** — `fairchem.data.oc.core.AdsorbateSlabConfig` places adsorbate at N sites
5. **Relaxation** — ALL N generated configs relaxed independently
6. **Selection** — Lowest energy among relaxed configs is the answer

Key difference from AdsMind: NO iterative closed-loop. The LLM plans once, generates N configs, relaxes all, picks the best. There is a `solution_reviewer` function for iterative refinement but it is NOT wired into the main loop.

### Relaxation Protocol Comparison (Source-Verified)

| Parameter | Adsorb-Agent (original) | AdsMind (ablation runs) | Action in fork |
|-----------|------------------------|------------------------|----------------|
| MLFF | EquiformerV2-31M-S2EF-OC20-All+MD | MACE-MP-0 small | Replace with MACE |
| Calculator | OCPCalculator (fairchem) | MACECalculator (mace-torch) | Replace |
| Optimizer | BFGS | BFGS | Same, no change |
| fmax | 0.05 eV/A | 0.10 eV/A | Change to 0.10 |
| max_steps | 100 | 200 | Change to 200 |
| Precision | float64 (CUDA) | float32 (macOS) | Change to float32 |
| Device | GPU (cpu=False) | CPU | Change to cpu |
| **Constraints** | **NONE** (FixAtoms lost) | FixAtoms (bottom 1/3 slab) | **Must add FixAtoms** |
| MD warmup | None | None (md_steps=0 on CPU) | Same, no change |
| Dispersion | N/A (EquiformerV2) | Disabled | Disabled |
| Trajectory | First+last frame only | Full trajectory | Keep original behavior |

#### CRITICAL: Constraint Gap (Biggest Hidden Difference)

Source analysis reveals that Adsorb-Agent runs **completely unconstrained relaxation**:

1. `fairchem/data/oc/core/slab.py:set_fixed_atom_constraints()` correctly sets `FixAtoms(mask=[tag==0])` on the bare slab
2. BUT `adsorbate_slab_config.py:place_adsorbate_on_site()` line 237 creates the adslab via `slab_c + adsorbate_c` — ASE's `+` operator **drops all constraints**
3. `utils.py:relax_adslab()` never re-applies any constraints
4. Result: ALL atoms (including bulk) move freely during BFGS

AdsMind uses `FIXED_BOTTOM_FRACTION = 1.0 / 3.0` (from `src/tools/constants.py`), fixing the bottom third of slab atoms.

### Steps

#### 2.1 Clone and set up CatalystAIgent

```bash
cd /home/zongmin
git clone https://github.com/hoon-ock/CatalystAIgent.git
cd CatalystAIgent
git clone https://github.com/hoon-ock/fairchem-forked.git

# Create isolated conda env
conda create -n adsorbagent python=3.10 -y
conda activate adsorbagent
pip install -r requirements.txt
pip install mace-torch>=0.3.14
```

Note: `requirements.txt` pins `torch==2.6.0` with CUDA 12.1 extensions. The workstation has CUDA 12.1 so this should work. If torch-geometric extensions fail:

```bash
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv \
  -f https://data.pyg.org/whl/torch-2.6.0+cu121.html
```

#### 2.2 Modify relaxation backend

Edit `utils.py` — replace the `relax_adslab` function.

Original:

```python
from fairchem.core.models.model_registry import model_name_to_local_file
from fairchem.core.common.relaxation.ase_utils import OCPCalculator

def relax_adslab(adslab, model_name, save_path, memory_save=True):
    checkpoint_path = model_name_to_local_file(model_name, local_cache='/tmp/fairchem_checkpoints/')
    calc = OCPCalculator(checkpoint_path=checkpoint_path, cpu=False)
    adslab.calc = calc
    opt = BFGS(adslab, trajectory=save_path)
    opt.run(fmax=0.05, steps=100)
    ...
```

Replace with:

```python
from mace.calculators import mace_mp
from ase.constraints import FixAtoms
import numpy as np

# Match AdsMind src/tools/constants.py exactly
FIXED_BOTTOM_FRACTION = 1.0 / 3.0

# Cache calculator to avoid reloading per-structure (~5s load time)
_mace_calc = None

def _get_mace_calc():
    global _mace_calc
    if _mace_calc is None:
        _mace_calc = mace_mp(
            model="small",
            device="cpu",
            default_dtype="float32"
        )
    return _mace_calc

def relax_adslab(adslab, model_name, save_path, memory_save=True):
    # --- Apply AdsMind-matching constraints (bottom 1/3 of slab fixed) ---
    # This is MANDATORY. Original Adsorb-Agent has NO constraints because
    # AdsorbateSlabConfig's slab_c + adsorbate_c drops FixAtoms.
    tags = adslab.get_tags()
    slab_indices = [i for i, t in enumerate(tags) if t in (0, 1)]
    if slab_indices:
        slab_z = adslab.positions[slab_indices, 2]
        z_min, z_max = slab_z.min(), slab_z.max()
        z_threshold = z_min + (z_max - z_min) * FIXED_BOTTOM_FRACTION
        fixed = [i for i in slab_indices if adslab.positions[i, 2] < z_threshold]
        adslab.set_constraint(FixAtoms(indices=fixed))

    # --- MACE calculator (matching AdsMind: small, cpu, float32, no dispersion) ---
    adslab.calc = _get_mace_calc()

    # --- BFGS optimization (matching AdsMind: fmax=0.10, steps=200) ---
    opt = BFGS(adslab, trajectory=save_path)
    opt.run(fmax=0.10, steps=200)

    if memory_save:
        traj = ase.io.read(save_path, ':')
        reduced_traj = [traj[0], traj[-1]]
        if os.path.exists(save_path):
            os.remove(save_path)
        ase.io.write(save_path, reduced_traj, format='traj')
    return adslab
```

Also remove the `torch.no_grad()` wrapper and `torch.cuda.empty_cache()` calls in `adsorb_agent.py` since we are running on CPU.

#### 2.3 Create per-system YAML configs for 20 cases

Adsorb-Agent expects per-case YAML files with this format (from `config/example/ORR-1.yaml`):

```yaml
system_info:
  ads_smiles: '*OH'
  bulk_id: mp-126
  bulk_symbol: Pt
  miller: (1,1,1)
  num_site: 54
  shift: 0.167
  system_id: null
  top: true
```

The repo includes 5 example configs in `config/example/` that map to 5 of the 20 cases. For the remaining 15, Codex must create configs by:

1. Reading AdsMind's `research/agent_eval/manifests/cmu_manifest.csv` for surface names and SMILES
2. Looking up `bulk_id` (Materials Project ID) using `pymatgen.ext.matproj.MPRester` or the fairchem bulk database at `fairchem-forked/src/fairchem/data/oc/databases/pkls/bulks.pkl`
3. Extracting `shift` and `top` from AdsMind's pre-built slab XYZ files using ASE:

```python
from ase.io import read
atoms = read("benchmark_slabs/09_Pt_111.xyz")
# shift and top can be inferred from the slab geometry
```

4. Setting `num_site` based on the Adsorb-Agent paper's Table 1 (column "configs_tested") or using a default of 54 (median from the paper)

The 5 example configs and their AdsMind case mappings:

| Example file | bulk_symbol | ads | AdsMind case |
|-------------|-------------|-----|-------------|
| ORR-1.yaml | Pt | OH | 09 |
| ORR-2.yaml | ? | OH | check |
| NRR-1.yaml | CuPd3 | NNH | 04 |
| NRR-2.yaml | ? | NNH | check |
| COMPLEX.yaml | (uses system_id) | ? | check |

Create all 20 configs in `config/cmu_benchmark/` directory.

SMILES mapping (AdsMind manifest → Adsorb-Agent format):

| AdsMind SMILES | Adsorb-Agent SMILES | Adsorbate |
|---------------|-------------------|-----------|
| `[H]` | `*H` | H |
| `[N]=[NH]` | `*N*NH` | NNH |
| `[OH]` | `*OH` | OH |
| `[CH2]CO` | MUST verify in adsorbates.pkl | CH2CH2OH |
| `CC=O` | MUST verify in adsorbates.pkl | OCHCH3 |
| `CN(C)N=O` | MUST verify in adsorbates.pkl | ONN(CH3)2 |

For cases 15-20 (complex adsorbates), the OC20 SMILES format is non-obvious. Codex MUST verify by searching fairchem's adsorbate database:

```python
import pickle
with open("fairchem-forked/src/fairchem/data/oc/databases/pkls/adsorbates.pkl", "rb") as f:
    ads_db = pickle.load(f)
# Search for matching adsorbates by formula or name:
for k, v in ads_db.items():
    if any(x in str(v) for x in ["CH2CH2OH", "C2H5O", "OCHCH3", "C2H4O", "ONN", "nitrosamine"]):
        print(k, v)
```

#### 2.4 Update all path references

The default `config/adsorb_agent.yaml` has hardcoded paths to the original author's machine. Create `config/adsorb_agent_cmu.yaml` with updated paths:

```yaml
agent_settings:
  provider: "openai"
  version: "gpt-4o"
  gnn_model: "mace-mp-0-small"
  mode: "llm-guided"
  critic_activate: true
  random_ratio: 0.2
  init_multiplier: 1.0

paths:
  question_path: "/home/zongmin/CatalystAIgent/reasoning/reasoning.txt"
  knowledge_path: "/home/zongmin/CatalystAIgent/reasoning/knowledge.txt"
  metadata_path: null
  bulk_db_path: "/home/zongmin/CatalystAIgent/fairchem-forked/src/fairchem/data/oc/databases/pkls/bulks.pkl"
  ads_db_path: "/home/zongmin/CatalystAIgent/fairchem-forked/src/fairchem/data/oc/databases/pkls/adsorbates.pkl"
  save_dir: "/home/zongmin/CatalystAIgent/results/cmu_benchmark"
  system_dir: "/home/zongmin/CatalystAIgent/config/cmu_benchmark"
```

#### 2.5 Create secret_keys.py

```python
openapi_key = "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"
anthropic_key = "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"
deepseek_key = ""
```

#### 2.6 Set random seed for reproducibility

Add at the top of `adsorb_agent.py`, after imports:

```python
np.random.seed(42)
torch.manual_seed(42)
```

#### 2.7 Run Adsorb-Agent with GPT-4o (original paper LLM)

```bash
tmux new-session -d -s adsorbagent

cd /home/zongmin/CatalystAIgent
conda activate adsorbagent
python adsorb_agent.py --path config/adsorb_agent_cmu.yaml
```

Use GPT-4o first (matching the original Adsorb-Agent paper) to establish the baseline. Each case generates N configs (paper reports 6-41, median ~20), each relaxed with MACE-small on CPU (~5-30s per relaxation). Total runtime: ~2-4 hours for 20 cases.

**Run count**: 1 run per case initially. If time permits, run 3x per case for mean±std (matching the paper's 3-run protocol).

**Failure handling**: If `AdsorbateSlabConfig` fails to find sites (cutoff_multiplier exceeds 1.3), the code returns None and skips the case. Record all skipped cases — they indicate SMILES/bulk_id/site_type mismatches that need debugging.

#### 2.8 (Optional) Run with GPT-5.4 for backend-controlled comparison

After the GPT-4o run completes, optionally rerun with GPT-5.4 to enable same-LLM comparison with AdsMind:

```yaml
agent_settings:
  provider: "openai"
  version: "gpt-5.4"
```

This isolates the search strategy variable: same LLM, same physics, different agent architecture.

#### 2.9 Postprocess and compare

```bash
python postprocess.py --dir results/cmu_benchmark/
```

Build comparison following `research/EXPERIMENT_PLAN.md` Section 3.3:

- For each of the 15 overlapping cases, extract Adsorb-Agent-MACE best energy
- Compare with AdsMind Full variant best energy (from `research/results/*/ablation_summary.csv`)
- Statistical tests (as defined in EXPERIMENT_PLAN.md):
  - Wilcoxon signed-rank test on energy differences (paired, n=15)
  - McNemar's test on success rate
  - Rank-biserial correlation for effect size
  - 95% bootstrap CI on median difference
  - Benjamini-Hochberg FDR correction
- Output: `research/results/comparison_stats.json`
- Also record per-case: number of configs relaxed, total MACE compute time, LLM token count — needed for cost/efficiency comparison in the paper

---

## Task 3: Commit and Push

After both tasks complete:

```bash
cd /path/to/AdsMind

# Rename old Gemini data
mv research/results/ocd_gmae_gemini_ablation_v1 \
   research/results/ocd_gmae_gemini_ablation_v1_aihubmix_archived

git add -A
git commit -m "data: Gemini OCD-GMAE v2 (Vertex AI direct) + Adsorb-Agent MACE comparison

- Reran 50 Gemini OCD-GMAE runs via Vertex AI direct API (replacing AiHubMix proxy)
- Archived old proxy-affected data as ocd_gmae_gemini_ablation_v1_aihubmix_archived
- Forked CatalystAIgent with MACE-MP-0 small backend (matching AdsMind protocol)
- Added FixAtoms constraints (bottom 1/3 slab) missing from original Adsorb-Agent
- Ran Adsorb-Agent on 20 CMU benchmark cases under identical physics
- Added comparison results and statistical analysis

Co-Authored-By: Codex <noreply@openai.com>"

git push origin main
```

---

## Execution Priority

1. **Task 1 first** (Gemini rerun) — straightforward, just infrastructure change
2. **Task 2 second** (Adsorb-Agent) — more complex, requires code modification and debugging
3. Both can run in parallel tmux sessions if Task 1's Vertex AI auth is resolved quickly

## Known Risks

1. **Vertex AI auth**: Token may expire; Codex may need `gcloud auth application-default login`
2. **fairchem-forked install**: May have issues on Ubuntu 22.04 / CUDA 12.1 with torch-geometric extensions
3. **Path dependencies**: ALL paths in Adsorb-Agent configs are hardcoded to `/home/hoon/`. Must be updated to `/home/zongmin/CatalystAIgent/`
4. **bulk_db_path / ads_db_path**: These pickle databases ship with fairchem-forked but the paths must point to the cloned location
5. **Constraint gap (CRITICAL)**: If Codex forgets to add FixAtoms in `relax_adslab`, the relaxation is unconstrained and energies are incomparable with AdsMind. `AdsorbateSlabConfig` uses `slab_c + adsorbate_c` which drops constraints — they must be re-applied inside `relax_adslab`, not before
6. **FIXED_BOTTOM_FRACTION**: Must be `1.0 / 3.0` (0.333), NOT 0.3. This matches `src/tools/constants.py` exactly
7. **Platform float32**: We explicitly use float32 on Linux even though the platform default is float64 — this is intentional to match existing macOS data
8. **SMILES format**: AdsMind uses standard SMILES (`[H]`, `[OH]`), Adsorb-Agent uses OC20-style with `*` for binding atoms (`*H`, `*OH`). The mapping must be correct for fairchem's adsorbate database lookup
9. **Vertex AI model version**: May differ from AiHubMix's Gemini 2.5 Pro. Acceptable since CMU and OCD-GMAE serve different analytical purposes
