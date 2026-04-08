# AdsMind: Closed-Loop Multi-Agent Framework for Autonomous Adsorption Configuration Search

**Target Journal**: JCTC

**Working Title (alternatives)**:
- AdsMind: Autonomous Adsorption Configuration Discovery via Closed-Loop LLM-MLFF Feedback
- Beyond Single-Shot Prediction: A Self-Correcting Multi-Agent System for Surface Adsorption

---

## Core Idea

LLM-based agents can propose adsorption configurations, but they carry **systematic chemical reasoning biases** — preferring high-symmetry sites, ignoring surface composition effects, and failing to learn from calculation outcomes.

AdsMind closes the loop: each MLFF relaxation result feeds back into the LLM planner, enabling the system to **detect its own mistakes** (Chemical Slip), **avoid repeating them** (FORBID constraints), and **know when to stop** (autonomous termination).

This is not a competitor to Adsorb-Agent — it is a **complementary paradigm**: they reduce search space via single-shot reasoning; we refine solutions via iterative physical feedback.

## Experiment Priority

| Priority | Task | Status | Deadline Sensitivity |
|----------|------|--------|---------------------|
| **P0 (Must)** | CMU 20-surface benchmark | To rerun | Blocks everything |
| **P0 (Must)** | Head-to-head vs Adsorb-Agent | Depends on P0 above | Core claim |
| **P0 (Must)** | DFT validation (3–5 systems) | Bowen leading | Philippe explicitly requested |
| **P0 (Must)** | Ablation study (3–5 systems) | Not started | Philippe explicitly requested |
| **P1 (Recommended)** | OC dataset evaluation (~50 systems) | Not started | Strengthens story significantly |
| **P1 (Recommended)** | Multi-model comparison (SI) | Not started | Reviewer will ask |
| **P2 (Nice-to-have)** | Literature reproduction (published DFT results) | Not started | If time allows |

**OCD-GMAE Dataset Overview** (used in Section 3.3 OC Stress Test):

- Unique catalyst surfaces (Surface Num.): 967 (covering 54 elements)
- Adsorbate species (Adsorbate Num.): 74
- Total surface/adsorbate combinations (System Num.): 973

---

## Full Paper Outline

---

### 1. Introduction — Why Single-Shot LLM Reasoning Is Not Enough

#### 1.1 Adsorption Configuration Search Matters

- Heterogeneous catalysis, energy storage, corrosion — all begin with finding stable adsorbate-surface configurations
- Combinatorial explosion: multiple sites (ontop/bridge/hollow) x surface atoms x adsorbate orientations x conformers
- Traditional approaches: exhaustive enumeration or heuristic sampling — computationally expensive, no guarantee of global minimum

#### 1.2 LLM-Driven Methods: Promise and Limitations

- LLMs encode chemical intuition from training data
- Adsorb-Agent (Ock et al., Digital Discovery, 2026): first LLM agent for adsorption — 84% success rate, 27% search space reduction
- **But**: open-loop architecture — LLM proposes once, calculations run, no feedback
- Consequences:
  - Dissociated/isomerized structures are filtered out, not learned from
  - No mechanism to detect or correct systematic biases
  - Cannot distinguish "calculation failed" from "site is thermodynamically unstable"

#### 1.3 Our Contribution: Closing the Loop

AdsMind introduces three mechanisms absent in prior work:

1. **Chemical Slip detection** — identifies when relaxation moves the adsorbate to a different site than planned, diagnosing LLM reasoning errors in real time
2. **FORBID constraints** — prevents re-exploration of sites proven unstable by prior iterations
3. **Autonomous termination** — stops exploration when convergence is detected, without fixed budget

**Central Thesis**:

> Iterative physical feedback transforms LLM chemical reasoning from educated guessing into evidence-based refinement. The resulting closed-loop system finds equal or lower energy configurations with fewer wasted calculations.

**Key framing**: complementary to Adsorb-Agent, not competitive. They reduce search space; we refine within it.

---

### 2. Methods — The AdsMind Framework

#### 2.1 Framework Overview (→ **Fig. 1**: Architecture Diagram)

Five-node LangGraph state machine:

```
Pre-Processor → Planner (LLM) → Plan Validator → Tool Executor → Final Analyzer
                    ↑                                    |
                    └──────── feedback loop ──────────────┘
```

- **Pre-Processor**: surface analysis via AutoAdsorbate shrinkwrap algorithm; identifies available site types and surface composition
- **Planner (LLM)**: receives full history of prior attempts with outcome tags; proposes next configuration or terminates
- **Plan Validator**: enforces chemical/geometric constraints before calculation (site-atom alignment, deduplication)
- **Tool Executor**: structure generation (AutoAdsorbate) → MACE-MP relaxation → bond integrity analysis → site classification
- **Final Analyzer**: generates scientific report with caveats (energy degeneracy, metastability, surface heterogeneity)

#### 2.2 Chemical Slip Detection

- **Definition**: mismatch between LLM-planned adsorption site and actual site after MLFF relaxation
- Detection: compare (planned_site_type, planned_surface_atoms) vs (actual_site_type, actual_surface_atoms)
- **Physical meaning**: the planned site is a saddle point or local maximum on the PES — the adsorbate slides to a nearby minimum
- Each slip is tagged in the iteration history: `[Unstable Site Warning]`
- The LLM learns which chemical environments are unstable for a given adsorbate

#### 2.3 FORBID Constraints

- After a Chemical Slip, the site type + surface atom combination is added to a FORBID list
- Planner is explicitly instructed: "Do NOT test {Cu-Pd bridge} type sites again"
- Validator rejects plans that violate FORBID constraints
- **Effect**: search space narrows with each iteration, focusing on chemically meaningful regions

#### 2.4 Autonomous Termination Logic

The planner triggers `TERMINATE` when:
- Current best matches previous best in both energy (within 0.05 eV) and geometry
- All major high-symmetry site types have been explored
- No chemical reasoning remains to motivate further exploration
- MAX_RETRIES (5) reached

#### 2.5 Computational Details

**MLFF**:
- MACE-MP-0 medium model
- Precision: float64 (Linux/CUDA), float32 (macOS/Apple Silicon)
- Optimizer: BFGS, fmax = 0.05 eV/A (GPU) / 0.10 eV/A (CPU)
- Bottom 1/3 of slab fixed; vacuum ≥ 15 A

**DFT** (validation subset):
- VASP 6.x, PBE + D3(BJ) dispersion correction
- ENCUT = 500 eV, k-points: 6x6x1 (Monkhorst-Pack)
- EDIFF = 1E-5 eV, EDIFFG = -0.02 eV/A
- Strategy: MACE-MP relaxed structures as initial guess → full DFT relaxation

**LLM**:
- Default: Gemini 2.5 Pro (production) — chosen for strong structured-output compliance, low cost per token, and competitive chemical reasoning in preliminary tests
- Temperature: 0.0 (deterministic)
- Multi-model comparison in SI (GPT-5.4, Claude Sonnet/Opus 4.6, Gemini 3.1 Pro/Flash Preview, open-source: Qwen 3.5, GLM 5, etc.) — purpose is to show that the closed-loop architecture improves performance **regardless of LLM backend**, and to generate Chemical Slip statistics across models

---

### 3. Results

---

#### 3.1 CMU Benchmark Replication (→ **Fig. 2** + **Table 1**)

- 20 surfaces from Adsorb-Agent benchmark (same test set for fair comparison) + 1 additional CuZnO complex multi-metal oxide system
- **Note**: the exact 20 systems are from Adsorb-Agent SI Table S1. Previous runs completed all 20 (19 succeeded, 1 failed), but run logs and full trajectories were not saved. Need to rerun to obtain publishable data.
- Systems span: monometallic (Pt, Pd, Au, Ag), intermetallic (Mo3Pd, CuPd3, CoPt, Ru3Mo, Au2Hf, Al3Zr), and others from the original benchmark
- Adsorbates: H, NNH, OH, OCHCH3, CH2CHCH3, CHO, and larger molecules
- Metrics: best adsorption energy found, number of iterations, Chemical Slip frequency, dissociation events

**Table 1**: Summary of 20 test systems — surface composition, miller index, adsorbate, best energy, binding site, Chemical Slip occurrence, PES classification (convergent / competing / counter-intuitive)

**Key results to report**:
- Success rate (% of systems where AdsMind finds energy within X eV of reference)
- Lower energy discovery rate (% where AdsMind finds lower energy than exhaustive enumeration)
- Chemical Slip prevalence (preliminary observation: high across intermetallic surfaces — exact statistics pending full rerun)
- Dissociation rate (preliminary observation: significant fraction of systems — exact statistics pending full rerun)

---

#### 3.2 Head-to-Head Comparison with Adsorb-Agent (→ **Fig. 5** + **Table 2**)

Direct comparison on the same 20 surfaces:

- **Energy**: side-by-side best energies — where AdsMind finds lower, equal, or higher
- **Efficiency**: number of LLM calls and MLFF relaxations per system
- **Robustness**: how each method handles dissociation/isomerization (AdsMind learns from it; Adsorb-Agent filters it out)
- **Failure analysis**: specific cases where Adsorb-Agent fails but AdsMind succeeds (and vice versa)

**Table 2**: Quantitative comparison — energy difference, iteration count, success rate, search space reduction ratio

**Fig. 5**: Case studies — 2-3 systems where closed-loop feedback makes the critical difference
- Example: surface with strong Chemical Slip (e.g., Mo3Pd) where iterative FORBID narrows search to correct site
- Example: complex adsorbate where dissociation detection prevents false minimum

**Key message**: AdsMind's advantage is largest on intermetallic/complex surfaces where LLM priors are least reliable and physical feedback is most informative.

---

#### 3.3 Stress Test on OC Dataset (→ **Table 3**) [P1 — Recommended]

The CMU benchmark (20 curated surfaces) tests basic competence. To probe robustness and generalization, we evaluate AdsMind on a larger, more diverse subset from the Open Catalyst (OC) dataset.

- **Dataset**: ~50 systems sampled from OCD-GMAE, a subset of OC20-Dense (973 unique adsorption entries, 967 surfaces covering 54 elements, 74 adsorbate species), covering a wider range of surface compositions, miller indices, and adsorbate sizes
- **Sampling strategy**: stratified by surface type (monometallic / bimetallic / ternary) and adsorbate complexity (atomic / small molecule / polyatomic)
- **Ground truth**: OC provides DFT-relaxed trajectories and final adsorption energies for each system — these serve as reference values

**Purpose**: if AdsMind performs well on CMU's curated benchmark but struggles on OC's diverse set, this reveals where LLM chemical priors break down at scale. Conversely, if performance holds, it strengthens the generalization claim.

**Key analysis**:
- Success rate stratified by surface complexity
- Chemical Slip frequency vs surface type — does slip rate increase on less-studied compositions?
- Comparison with Adsorb-Agent on the same OC subset (if feasible within timeline)

**Fallback**: if full OC evaluation is not feasible before submission, present preliminary results on a smaller subset (~20 systems) and flag the full evaluation as follow-up work.

---

#### 3.4 DFT Validation (→ **Fig. 4**: Scatter Plot)

3–5 representative surfaces validated with full DFT relaxation.

**Selection rationale**: systems chosen to cover four independent axes of variation, so that validation is not cherry-picked:

| Axis | System | Why this one |
|------|--------|-------------|
| Monometallic baseline | Pt(111) + OH | Well-studied ORR surface; abundant DFT literature for cross-check |
| Facet sensitivity | Pt(100) + OH | Same adsorbate on a different facet — tests whether MACE-MP captures facet-dependent ranking |
| Intermetallic + small adsorbate | Mo3Pd(111) + H | NRR-relevant; strong Chemical Slip observed — stress-tests MACE-MP on a surface where LLM priors are weakest |
| Intermetallic + larger adsorbate | Mo3Pd(111) + NNH | Same surface, polyatomic adsorbate — probes whether ranking holds for multi-atom binding |
| Bimetallic ORR | CoPt(111) + OH | Intermetallic with practical catalytic relevance; bridges monometallic and complex cases |

**Validation metrics**:
- MACE-MP vs DFT energy ordering consistency (target: ≥ 90%)
- Absolute energy error (target: < 0.1 eV)
- Structural RMSD (target: < 0.2 Å)

**Fig. 4**: Scatter plot of MACE-MP predicted energy vs DFT energy for all validated configurations, with parity line and error bars. Inset: structural overlays for 2–3 representative cases.

**Key message**: MACE-MP energy rankings are reliable enough to guide the search, even if absolute energies deviate. The agent's role is to find the right region of configuration space; DFT confirms the ranking.

---

#### 3.5 Ablation Study (→ **Fig.** or **Table 4**)

Quantify the contribution of each AdsMind component:

**Design**: 2x2 factorial on 3-5 representative systems

| Variant | Chemical Slip | FORBID | Termination |
|---------|:---:|:---:|:---:|
| Full AdsMind | ON | ON | ON |
| No Slip Detection | OFF | OFF | ON |
| No FORBID | ON | OFF | ON |
| No Termination | ON | ON | OFF (fixed budget) |
| Baseline (single-shot) | OFF | OFF | OFF |

**Metrics per variant**:
- Best energy found
- Number of iterations to converge
- Number of wasted calculations (configurations that didn't improve the best)
- Success rate

**Key message**: each component contributes independently; Chemical Slip detection is expected to provide the largest single improvement on intermetallic surfaces; FORBID reduces wasted iterations; termination saves compute without sacrificing quality. (Confirm or revise after data is collected.)

---

### 4. Discussion

#### 4.1 Chemical Slip as a Proxy Metric for LLM Chemical Reasoning

- Chemical Slip is not just a correction mechanism — it reveals **where LLM chemical intuition breaks down**
- High slip rates on specific surface atom combinations indicate systematic training data gaps
- **Key insight**: Chemical Slip frequency, stratified by surface type and adsorbate, can serve as a **quantitative proxy for LLM chemical reasoning quality** — independent of any downstream task metric
- Comparison across LLM backends (SI-5): if model A has lower slip rate than model B on intermetallic surfaces, model A has better internalized chemistry for those systems. This is a more fine-grained evaluation than "did the agent find the global minimum"
- This framing turns a byproduct of our system into a **standalone methodological contribution**: a physically grounded way to evaluate LLM chemical knowledge, going beyond text-based benchmarks (e.g., ChemBench) that test factual recall rather than applied reasoning
- Potential community use: other groups can report Chemical Slip statistics on their own systems to benchmark LLM chemical reasoning in specific domains

#### 4.2 Closed-Loop vs Open-Loop: A Paradigm Difference

- Open-loop (Adsorb-Agent): fast, parallelizable, good for well-understood surfaces
- Closed-loop (AdsMind): slower per iteration, but finds better solutions on complex surfaces
- Not mutually exclusive — could combine: Adsorb-Agent for initial proposals → AdsMind for iterative refinement

#### 4.3 MLFF as Surrogate: When Does It Work?

- DFT validation shows MACE-MP energy rankings are generally reliable
- Failure modes: dispersion-dominated binding, strongly correlated systems
- The agent's value is orthogonal to MLFF accuracy — it optimizes search strategy, not the energy function

#### 4.4 Limitations

- MACE-MP accuracy ceiling on certain systems (e.g., f-electron metals)
- LLM API cost and latency (quantify in SI)
- Current implementation: only flat/stepped surfaces, no defects or nanoparticles
- Single adsorbate per surface (no co-adsorption)

---

### 5. Conclusion

- AdsMind demonstrates that **closing the feedback loop** between LLM reasoning and physical simulation significantly improves adsorption configuration search
- Chemical Slip detection turns LLM errors into learning signals
- Head-to-head with Adsorb-Agent: comparable or better results, especially on complex surfaces
- DFT validation confirms MLFF-guided search is reliable for configuration ranking
- Open-source: code, structures, and logs available at GitHub

---

### Data Availability

- GitHub: https://github.com/AI4QC/AdsMind
- All surface structures, trajectory files, and agent logs
- DFT input/output files for validated systems

---

## Figures & Tables Plan

| # | Type | Content | Section | Owner | Priority |
|---|------|---------|---------|-------|----------|
| **Fig. 1** | Schematic | AdsMind architecture — 5-node state machine with feedback loop | 2.1 | Yuyang | P0 |
| **Fig. 2** | Bar/table | CMU benchmark results: 20 surfaces, energies, iterations, slip rates | 3.1 | Zongmin | P0 |
| **Fig. 3** | Diagram | Workflow context — how Chemical Slip / FORBID / termination interact across iterations | 2.2–2.4 | Yuyang | P0 |
| **Fig. 4** | Scatter | DFT validation: MACE-MP vs DFT energies with parity line | 3.4 | Bowen + Zongmin | P0 |
| **Fig. 5** | Case study | Head-to-head: cases where AdsMind succeeds and Adsorb-Agent fails | 3.2 | Zongmin | P0 |
| **Table 1** | Data | 20 test systems summary: surface, adsorbate, energy, site, slip, PES type | 3.1 | Zongmin | P0 |
| **Table 2** | Comparison | AdsMind vs Adsorb-Agent: energy, iterations, success rate | 3.2 | Zongmin | P0 |
| **Table 3** | Data | OC dataset stress test: success rate by surface type, slip frequency | 3.3 | Zongmin | P1 |
| **Table 4** | Ablation | Component contribution: full vs variants on 3–5 systems | 3.5 | Zongmin | P0 |

---

## Supporting Information Plan

| SI Section | Content | Priority |
|-----------|---------|----------|
| SI-1 | Extended methods: full prompt templates, MACE-MP parameters, AutoAdsorbate settings | Must |
| SI-2 | Complete benchmark data for all 20 CMU surfaces (energy tables, iteration logs) | Must |
| SI-3 | DFT validation extended data: all configurations, INCAR settings, convergence | Must |
| SI-4 | Ablation study full statistics and interaction effects | Must |
| SI-5 | LLM model comparison: 4–5 models on representative systems + Chemical Slip statistics per model | Recommended |
| SI-6 | Cost analysis: LLM tokens, MLFF compute time, human effort | Recommended |
| SI-7 | OC dataset extended results: full system list, per-system metrics, failure cases | Recommended |
| SI-8 | Failure case analysis: systematic classification of failure modes | Optional |

---

## What Makes This Paper Work

1. **Clear contribution**: not "yet another LLM agent" — a specific architectural innovation (closed-loop feedback) with a specific mechanism (Chemical Slip)
2. **Fair comparison**: same benchmark, same surfaces, direct head-to-head with the only published competitor
3. **Escalating difficulty**: CMU benchmark (curated) → OC dataset (diverse) → DFT validation (ground truth) — a three-tier evaluation that preempts "but does it generalize?" reviewer concerns
4. **Physical validation**: DFT confirms that MLFF-guided search is meaningful, not just numerically self-consistent
5. **Ablation**: each component justified quantitatively, not just described
6. **Dual contribution**: the closed-loop architecture is contribution #1; Chemical Slip as a proxy metric for LLM chemical reasoning quality is contribution #2 — this gives the paper legs beyond the specific application
7. **Complementary framing**: positions AdsMind alongside Adsorb-Agent, not against it — reviewers from CMU's community won't feel attacked
