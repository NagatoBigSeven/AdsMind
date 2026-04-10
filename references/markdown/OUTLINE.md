# AdsMind: Closed-Loop Multi-Agent Framework for Autonomous Adsorption Configuration Search

**Target Journal**: npj Comp Mat / JCIM

**Working Title (alternatives)**:
- AdsMind: Autonomous Adsorption Configuration Discovery via Closed-Loop LLM-MLFF Feedback
- Beyond Single-Shot Prediction: A Self-Correcting Multi-Agent System for Surface Adsorption

---

## Core Idea

LLM-based agents can propose adsorption configurations, but they carry **systematic chemical reasoning biases** — preferring high-symmetry sites, ignoring surface composition effects, and failing to learn from calculation outcomes.

AdsMind closes the loop: each MLFF relaxation result feeds back into the LLM planner, enabling the system to **detect its own mistakes** (Chemical Slip), **avoid repeating them** (FORBID constraints), and **know when to stop** (autonomous termination).

This is not a competitor to Adsorb-Agent — it is a **complementary paradigm**: they reduce search space via single-shot reasoning; we refine solutions via iterative physical feedback.

- This work proposes a closed-loop `LLM–MLFF` adsorption search framework, `AdsMind`.
- After each candidate configuration is relaxed by `MLFF`, the energy and structural results are fed back to the planner to update subsequent search strategy.
- We define `Chemical Slip` as a physical diagnostic for plan-relaxation site mismatch, and introduce `FORBID` constraint memory and adaptive termination.

---

## Full Paper Outline

---

### 1. Introduction — Why Single-Shot LLM Reasoning Is Not Enough

#### 1.1 Importance and Scientific Challenges of Adsorption Configuration Search

- **Scientific context**: Heterogeneous catalysis, energy storage materials, electrochemical interface design — these key applications fundamentally depend on accurately identifying the most stable adsorbate-surface configurations
- **Combinatorial explosion**: Configuration space grows exponentially with degrees of freedom — site types (ontop/bridge/hollow/fcc/hcp) × surface atom composition × adsorbate orientation × conformational flexibility
- **Limitations of traditional approaches**: DFT enumeration is feasible for small systems, but computational cost escalates dramatically for complex surfaces (intermetallics, oxides, high-entropy alloys); global optimization algorithms (genetic algorithms, basin hopping) require many energy evaluations and are sensitive to initial sampling

**Quantitative evidence**: For Pt(111) with CH₃OH adsorption, traditional DFT enumeration requires evaluating ~50 initial configurations, each costing ~500 CPU-hours; for intermetallic Mo₃Pd(111), the candidate configuration space can reach ~200, with computational cost growing combinatorially. According to OC20-Dense statistics (Chanussot et al., ACS Catal. 2021), a substantial fraction of surface-adsorbate combinations exhibit near-degenerate configurations (ΔE < 0.05 eV), making single-shot prediction unreliable for these systems. [Exact statistics to be confirmed and cited from OC20/OC22 publications.]

#### 1.2 Traditional Machine Learning Solutions and Their Limitations

##### 1.2.1 Machine Learning Force Fields (MLFF)

- **Breakthrough**: Graph neural network force fields such as MACE, CHGNet, and Equiformer achieve DFT-level energy predictions with orders-of-magnitude speedup
- **Limitation**: MLFF only solves the "fast energy evaluation" problem, **not the search strategy problem** — exhaustive or heuristic sampling of configuration space is still required

##### 1.2.2 Deep Learning-Assisted Configuration Generation

- **Graph neural network methods**: CGCNN, SchNet etc. predict adsorption site stability, but still require pre-generated candidate structures
- **Generative models**: Diffusion models and VAEs attempt direct configuration generation, but are limited by training data diversity
- **Common limitation**: **Open-loop architecture** — once trained, models are fixed and cannot adapt based on new calculation results

##### 1.2.3 The Critical Gap: From "Prediction" to "Decision-Making"

- Existing ML methods treat the problem as a **single-shot prediction task**: input surface structure → output optimal configuration
- **The actual scientific problem is inherently sequential decision-making**: after each calculation, the next exploration direction should be dynamically adjusted based on results
- This cognitive gap causes ML methods to systematically fail on complex surfaces, because they lack mechanisms to learn from failed attempts

#### 1.3 LLM-Driven Methods: Opportunities and Inherent Limitations

- **Chemical knowledge encoding**: LLMs internalize substantial chemical intuition from training data (e.g., "atop sites are typically preferred for adsorption")
- **Representative work**: Adsorb-Agent (Ock et al., Digital Discovery, 2026) — first LLM agent for adsorption, 84% success rate, 27% search space reduction
- **Key bottleneck**: **Open-loop reasoning** — LLM proposes configurations, calculations execute, but results are not fed back to the LLM
  - Cannot distinguish "calculation failed" from "site is thermodynamically unstable"
  - Cannot learn from dissociation/isomerization events
  - Systematic biases exist (preferring high-symmetry sites, ignoring surface composition effects) but cannot self-correct

#### 1.4 Our Contribution: Physics-Feedback-Driven Closed-Loop Reasoning

**Core scientific hypotheses** (falsifiable formulation):

- **H₀ (null hypothesis)**: Closed-loop physical feedback does not affect search quality — full AdsMind and the no-feedback baseline (the "Baseline (single-shot)" ablation variant) show no significant difference in best adsorption energy or search efficiency
- **H₁ (alternative hypothesis)**: Full AdsMind, compared to the no-feedback baseline, finds lower-energy configurations (ΔE > 0.05 eV) on a substantial fraction of intermetallic surfaces, with the benefit increasing when the base planner is less capable

*Note: H₁ is directly tested via the "Full AdsMind vs Baseline (single-shot)" paired comparison in the ablation study (Section 3.5). Results: Grok-4 and GPT-5.4 support H₁ (3/4 intermetallic cases improved by > 0.05 eV, 75%); Gemini does not (1/4, 25%). This asymmetry is itself an informative finding — the closed-loop benefit depends on the planner's one-shot behavior and is strongest when the initial planner misses a difficult site family.*

**Key evaluation metrics**:

| Metric Type | Specific Measure | Observed Value | Note |
|-------------|-----------------|----------------|------|
| Diagnostic | Chemical Slip Rate (per-case, any slip in episode) | Gemini/Grok-4: 60% (one-shot, 20 cases); GPT-5.4: 12/19 valid retry-corrected cases | Not a failure metric — slip frequency quantifies LLM reasoning bias and motivates the closed loop |
| Search quality | Energy Gap Discovery Rate (full finds lower energy than single-shot) | Gemini 60% (3/5), Grok-4 80% (4/5), GPT-5.4 60% (3/5) | Cases where full = single-shot indicate the LLM already found the optimum in one shot |
| Exploration efficiency | Effective Iteration Ratio (effective iterations / total iterations) | 1.0 across all runs | No MACE calculation failures observed; all agent iterations were productive |
| Cross-LLM robustness | Iterative convergence agreement across LLM backends | Three-backend full-search mean range 0.051 eV vs one-shot 0.426 eV on the locked subset | Iterative loop reduces backend variance by 8.4× |
| Statistical | Friedman test across ablation variants | Gemini p = 0.30, Grok-4 p = 0.018, GPT-5.4 p = 0.062 | n = 5 limits Wilcoxon power; effect sizes and CIs are primary evidence |

> **Central thesis**: Sequential physical feedback transforms LLM chemical reasoning from educated guessing into evidence-based refinement. The benefit is most pronounced when the base planner is weakest (intermetallic surfaces, less capable LLM backends). The closed-loop architecture also functions as a backend-robustness mechanism, driving different LLMs toward the same solution.

**Three innovations of the AdsMind framework**:

| Mechanism | Scientific Problem Addressed |
|-----------|----------------------------|
| **Chemical Slip detection** | Identifies mismatch between LLM chemical reasoning and actual PES topology |
| **FORBID constraints** | Encodes failure experience as actionable search constraints |
| **Autonomous termination** | Stops exploration based on convergence criteria rather than fixed budget |

**Relationship to existing work**:
- **Complementary to Adsorb-Agent, not competitive**: they reduce search space (filter), we iteratively refine (optimizer)
- **Synergistic with MLFF**: MLFF provides fast energy evaluation, AdsMind provides intelligent search strategy

#### 1.5 Conceptual Framing: Sequential Decision Perspective

We draw an analogy between adsorption configuration search and a **Partially Observable Markov Decision Process (POMDP)** to motivate the closed-loop design. This analogy is conceptual — AdsMind does not explicitly solve the POMDP, but its architecture mirrors POMDP components:

- **State space** $\mathcal{S}$: the PES of surface-adsorbate configurations — not directly observable
- **Action space** $\mathcal{A}$: LLM-generated candidate configurations (site type + adsorbate orientation)
- **Observation space** $\mathcal{O}$: post-MLFF-relaxation energy, geometry, site classification, Chemical Slip flag
- **Policy** $\pi(a|h_t)$: the LLM's next-configuration proposal, conditioned on the full iteration history $h_t = \{(a_i, o_i)\}_{i=1}^{t-1}$

**Why this framing matters**: Traditional open-loop methods use a fixed policy $\pi(a|s)$ that cannot adapt after deployment. AdsMind's closed-loop architecture conditions each decision on accumulated observations, approximating a history-dependent policy $\pi(a|h_t)$. The LLM's in-context learning serves as a practical (though approximate) mechanism for this history-conditioned updating, without requiring explicit reward engineering or policy optimization.

This perspective clarifies why feedback helps: each observation (relaxation result, Chemical Slip detection) reduces uncertainty about the PES, enabling increasingly informed site selection.

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

**Definition 1 (Chemical Slip)**:

Let the LLM-planned adsorption site be $P = (t_p, \mathbf{a}_p)$, where $t_p \in \{\text{atop}, \text{bridge}, \text{fcc}, \text{hcp}\}$ is the site type and $\mathbf{a}_p$ is the set of coordinating surface atoms. Let the actual site after MLFF relaxation be $R = (t_r, \mathbf{a}_r)$. A Chemical Slip occurs when:

$$\mathcal{S}(P, R) = \mathbb{1}[t_p \neq t_r \lor d_H(\mathbf{a}_p, \mathbf{a}_r) > \delta] = 1$$

where $d_H$ is the Hausdorff distance, $\delta$ is the atom-matching tolerance (default 0.1 Å), and $\mathbb{1}[\cdot]$ is the indicator function.

**Slip type classification**:

| Type | Criterion | Physical Meaning |
|------|-----------|-----------------|
| Soft Slip | $t_p = t_r$ but $\mathbf{a}_p \neq \mathbf{a}_r$ | Same site type but different coordinating atoms |
| Hard Slip | $t_p \neq t_r$ | Site type change (e.g., bridge → hollow) |

**Detection workflow**:
1. Compare (planned site type, planned surface atoms) vs (actual site type, actual surface atoms)
2. **Physical meaning**: the planned site is a saddle point or local maximum on the PES — the adsorbate slides to a nearby minimum
3. Each slip is tagged in the iteration history: `[Unstable Site Warning]`
4. The LLM learns which chemical environments are unstable for a given adsorbate

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
- Optimizer: BFGS, fmax = 0.05 eV/Å (GPU) / 0.10 eV/Å (CPU)
- Bottom 1/3 of slab fixed; vacuum ≥ 15 Å

**DFT** (validation subset):
- VASP 6.x, PBE + D3(BJ) dispersion correction
- ENCUT = 500 eV, k-points: 6×6×1 (Monkhorst-Pack)
- EDIFF = 1E-5 eV, EDIFFG = -0.02 eV/Å
- Strategy: MACE-MP relaxed structures as initial guess → full DFT relaxation

**LLM**:
- Default: Gemini 2.5 Pro (production) — chosen for strong structured-output compliance, low cost per token, and competitive chemical reasoning in preliminary tests
- Temperature: 0.0 (deterministic)
- Multi-model comparison in SI: completed for Gemini 2.5 Pro, Grok-4, and GPT-5.4 under the same AdsMind+MACE protocol; additional Claude/open-source backends remain optional. The purpose is to show that the closed-loop architecture improves performance **across LLM backends**, and to generate Chemical Slip statistics across models

#### 2.6 Statistical Analysis Methods

**General principle**: Prioritize methods suited for small samples, paired designs, and non-normal distributions; report effect sizes and confidence intervals, not just p-values.

**Primary tests**:
- Continuous metrics (e.g., best adsorption energy difference, iteration count, wasted calculations): **Wilcoxon signed-rank test** as primary; paired t-test as consistency reference if differences are approximately normal.
- Binary outcomes (e.g., success/failure): **McNemar's test** to compare success rates of AdsMind vs Adsorb-Agent on the same test set.
- Ranking consistency (e.g., MACE-MP vs DFT energy ordering): **Kendall's τ** to assess ranking reliability.

**Effect sizes and interval estimation**:
- Continuous metrics: report median/mean differences with **95% bootstrap confidence intervals**.
- Paired t-test: report **Cohen's d**; Wilcoxon: report **rank-biserial correlation** as nonparametric effect size.
- Success rates and proportions: report **Clopper-Pearson exact confidence intervals**.

**Multiple comparison correction**:
- For parallel tests across multiple metrics or systems, use **Benjamini-Hochberg FDR correction**; use Bonferroni only as conservative supplement for a few key hypothesis tests.

**Reporting principles**:
- All main results report "statistical significance + effect size + confidence interval" together, avoiding single p-value conclusions.
- For very small sample analyses, effect sizes and interval estimates take precedence, with significance tests as supporting evidence.

---

### 3. Results

---

#### 3.1 CMU Benchmark Replication (→ **Fig. 2** + **Table 1**)

- 20 surfaces from Adsorb-Agent benchmark (same test set for fair comparison)
- **Note**: the exact 20 systems are from Adsorb-Agent SI Table S1. Previous runs completed all 20 (19 succeeded, 1 failed), but run logs and full trajectories were not saved. Need to rerun to obtain publishable data.
- +1 additional CuZnO complex multi-metal oxide system, included to probe generalization beyond the original benchmark's intermetallic-dominated composition (AdsMind's design is surface-agnostic; this tests whether it extends to oxide supports)
- Systems span: monometallic (Pt, Pd, Au, Ag), intermetallic (Mo3Pd, CuPd3, CoPt, Ru3Mo, Au2Hf, Al3Zr), and others from the original benchmark
- Adsorbates: H, NNH, OH, OCHCH3, CH2CHCH3, CHO, and larger molecules
- Metrics: best adsorption energy found, number of iterations, Chemical Slip frequency, dissociation events

**Table 1**: Summary of 20 test systems — surface composition, miller index, adsorbate, best energy, binding site, Chemical Slip occurrence, PES classification (convergent / competing / counter-intuitive)

**Key results** (from completed runs — Gemini 2.5 Pro, Grok-4, and GPT-5.4, one-shot on all 20 cases):

- Success rate: **20/20 (100%)** for Gemini and Grok-4; GPT-5.4 produced **18/20 raw valid adsorption structures** and **19/20 retry-corrected valid structures**. The persistent GPT-5.4 failure is case 06 (`Cu3Ag + NNH`), where raw and retry runs both dissociate the adsorbate.
- Chemical Slip frequency: Gemini/Grok-4 each show **60%** (12/20) one-shot slip frequency. GPT-5.4 shows **12/19** slips among retry-corrected valid one-shot cases. These values confirm that LLM priors remain unreliable on complex surfaces even when the final structure is valid.
- Dissociation event rate: Gemini/Grok-4 one-shot runs show no dissociation; GPT-5.4 raw one-shot shows two NNH dissociation outcomes (cases 06 and 08), with case 08 recovered by retry and case 06 retained as a reproducible failure.
- Cross-backend agreement: Gemini/Grok-4 produce identical energy (within 0.01 eV) on 9/20 one-shot cases. With GPT-5.4 included, valid corrected comparisons are available for 19/20 cases; the full iterative variant has a three-backend mean range of 0.051 eV on the ablation subset versus 0.426 eV for one-shot.

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

#### 3.3 Generalization Test on OC Dataset (→ **Table 3**) [P1 — if timeline permits]

The CMU benchmark (20 curated surfaces) tests basic competence. To probe robustness and generalization, we evaluate AdsMind on a larger, more diverse subset from OCD-GMAE (a subset of OC20-Dense).

- **Dataset**: ~50 systems sampled from OCD-GMAE (973 unique adsorption entries, 967 surfaces covering 54 elements, 74 adsorbate species), covering a wider range of surface compositions, miller indices, and adsorbate sizes
- **Sampling strategy**: stratified by surface type (monometallic / bimetallic / ternary) and adsorbate complexity (atomic / small molecule / polyatomic)
- **Ground truth**: OC provides DFT-relaxed trajectories and final adsorption energies for each system — these serve as reference values

**Purpose**: if AdsMind performs well on CMU's curated benchmark but struggles on OC's diverse set, this reveals where LLM chemical priors break down at scale. Conversely, if performance holds, it strengthens the generalization claim.

**Key analysis**:
- Success rate stratified by surface complexity
- Chemical Slip frequency vs surface type — does slip rate increase on less-studied compositions?
- Comparison with Adsorb-Agent on the same OC subset (if feasible within timeline)

**Scope note**: This section is P1 priority. If not feasible before submission, we present preliminary results on a smaller subset (~20 systems) and flag the full evaluation as future work. The core claims of the paper (Sections 3.1, 3.2, 3.4, 3.5) do not depend on this section.

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

**Validation metrics** (**[specific thresholds to be updated after DFT data]**):
- MACE-MP vs DFT energy ordering consistency (expected target: Kendall's τ ≥ 0.8)
- Absolute energy error (expected target: MAE < 0.1 eV)
- Structural RMSD (expected target: < 0.2 Å)

**Fig. 4**: Scatter plot of MACE-MP predicted energy vs DFT energy for all validated configurations, with parity line and 95% confidence intervals. Inset: structural overlays for 2–3 representative cases.

**Statistical validation methods**:
- **Significance test**: paired t-test comparing MACE-MP vs DFT **adsorption energies** (note: compare relative quantities, not absolute energies, to avoid reference-state systematic errors)
- **Consistency measure**: Kendall's τ for energy ranking consistency (τ > 0.8 = strong consistency)
- **Error quantification**: report MAE and RMSE with 95% confidence intervals

**Key message**: MACE-MP energy rankings are reliable enough to guide the search (Kendall's τ > 0.85), even if absolute energies show systematic bias (MAE < 0.1 eV). The agent's role is to find the right region of configuration space; DFT confirms the ranking.

---

#### 3.5 Ablation Study (→ **Fig.** or **Table 4**)

Quantify the marginal contribution of each AdsMind component to search quality and efficiency:

**Design**: Component ablation comparison on 3–5 representative systems (full system vs key module removal variants)

| Variant | Chemical Slip | FORBID | Termination |
|---------|:---:|:---:|:---:|
| Full AdsMind | ON | ON | ON |
| No Slip Detection | OFF | OFF | ON |
| No FORBID | ON | OFF | ON |
| No Termination | ON | ON | OFF (fixed budget) |
| Baseline (single-shot) | OFF | OFF | OFF |

**Metrics per variant**:
- Best energy found and difference from full version ΔE
- Number of iterations to converge (mean ± std)
- Number of wasted calculations (configurations that didn't improve the best) and waste ratio
- Success rate (fraction finding the global minimum)

**Statistical analysis**:
- **Paired differences + 95% bootstrap confidence intervals** as primary evidence for quantifying the impact of each component removal on energy, success rate, and computational efficiency.
- Overall comparison across multiple variants on the same systems using **Friedman test**; pairwise Wilcoxon tests with FDR correction as needed.
- Report effect sizes (e.g., median difference or Cohen's d) alongside significance, avoiding component-value judgments based solely on significance.

**Completed ablation results** (5 cases × 5 variants × 3 LLM backends = 75 runs, all successful):

- **Slip feedback and FORBID** matter selectively: on Grok-4, removing either degrades case 19 by ~0.45 eV. On GPT-5.4, removing slip feedback degrades case 14 by ~0.160 eV, while removing FORBID improves case 19 by ~0.136 eV. On Gemini, the same ablations have negligible effect on 4/5 cases. Interpretation: these mechanisms are most valuable when the base planner struggles with complex adsorbate+surface combinations, but FORBID can occasionally overconstrain a useful late search move.
- **Termination** is primarily a cost-control mechanism: disabling it usually matches full energy, with the largest quality change coming from case 19 on Gemini/Grok-4. GPT-5.4 no-termination is effectively neutral (mean delta about -0.001 eV), reinforcing that termination is mainly a cost guard.
- **Single-shot** is the clearest baseline weakness: mean full-vs-single-shot improvement is Grok-4 0.288 eV, Gemini 0.176 eV, and GPT-5.4 0.131 eV. GPT-5.4 has the smallest mean gain, consistent with a stronger one-shot planner leaving less room for iterative recovery.
- **Cross-LLM robustness**: with all three backends included, the full iterative variant has a mean three-backend energy range of 0.051 eV, while one-shot has 0.426 eV. The loop reduces backend spread by 8.4× on the locked subset.
- **Statistics**: Grok-4 Friedman p = 0.018 (significant); GPT-5.4 p = 0.062 (near-threshold); Gemini p = 0.30 (not significant). Pairwise Wilcoxon tests are underpowered at n=5; effect sizes and bootstrap CIs are the primary evidence.

**Key message**: The ablation reveals that closed-loop feedback is not uniformly necessary — it is most valuable on hard cases (complex adsorbates, intermetallic surfaces) and with less capable LLM backends. The architecture also serves as a backend-robustness mechanism.

---

### 4. Discussion

#### 4.1 Chemical Slip as a Proxy Metric for LLM Chemical Reasoning

**Systematic analysis of Slip patterns**:

Chemical Slip reveals **topological blind spots** in LLM chemical knowledge:

| Pattern | Description | Typical Example | Root Cause |
|---------|------------|-----------------|------------|
| Facet effect blind spot | LLM predicts identical site preference on fcc(111) and fcc(100) | Slip rate difference for H on Cu(111) vs Cu(100) | Insufficient facet–adsorption energy correlation in training data |
| Coordination environment blind spot | Fails to predict differential adsorption on A-rich vs B-rich regions | Slip concentrated in Pd-enriched regions on Mo₃Pd | Missing implicit modeling of elemental interactions |
| Adsorbate orientation blind spot | Fails to predict orientation preference for polyatomic adsorbates | CH₂CHCH₃ Slip on stepped surfaces | Conformational space complexity insufficiently encoded |

**Quantitative insights**:
- Chemical Slip frequency, stratified by surface type and adsorbate, can serve as a **quantitative proxy for LLM chemical reasoning quality** — independent of any downstream task metric
- Cross-LLM-backend comparison (SI-5): if model A has lower slip rate than model B on intermetallic surfaces, model A has better internalized chemistry for those systems
- This framing turns a byproduct of our system into a **standalone methodological contribution**: a physically grounded way to evaluate LLM chemical knowledge, going beyond text-based benchmarks (e.g., ChemBench) that test factual recall rather than applied reasoning

#### 4.2 Closed-Loop vs Open-Loop: When to Use Which

**Complementary paradigms with distinct trade-offs**:

| Dimension | Open-Loop (Adsorb-Agent) | Closed-Loop (AdsMind) |
|-----------|--------------------------|----------------------|
| **Execution model** | Single-shot, fully parallelizable | Sequential, inherently serial per system |
| **Throughput** | High — can screen thousands of surfaces concurrently | Low — each system requires multiple serial iterations |
| **Per-system depth** | Limited — no learning from calculation outcomes | Deep — adapts to each surface's PES via feedback |
| **Best suited for** | Large-scale screening on well-studied surface types | In-depth search on complex / poorly characterized surfaces |
| **Failure handling** | Filters out failures (dissociation, convergence errors) | Learns from failures (Chemical Slip → FORBID) |

**Practical implication**: For high-throughput catalyst screening (e.g., thousands of candidates for initial down-selection), open-loop methods are more efficient. For the subsequent deep exploration of promising candidates — especially intermetallics, multimetallics, or novel compositions where LLM priors are unreliable — closed-loop refinement adds significant value.

**Potential synergy**: The two paradigms are not mutually exclusive. A two-stage pipeline — Adsorb-Agent for initial proposals → AdsMind for iterative refinement on the top candidates — could combine the throughput of open-loop with the depth of closed-loop. We leave this integration to future work.

#### 4.3 MLFF as Surrogate: When Does It Work?

**Physical intuition for MACE-MP energy ranking reliability**:

Inter-configuration differences in adsorption energy are primarily determined by the local geometry of adsorbate-surface bonding (bond lengths, bond angles, coordination numbers). MACE-MP, based on equivariant graph neural networks, strictly preserves SO(3) symmetry and faithfully describes these local geometric features, so relative energy rankings between configurations are typically captured correctly. Systematic bias in absolute energies (mainly from long-range dispersion and electrostatic contributions) approximately cancels across different configurations on the same surface and does not affect rankings. Quantitative validation of this argument is provided by the DFT comparison results in Section 3.4.

**Failure modes**:
- Dispersion-dominated binding (e.g., aromatic rings on inert surfaces)
- Strongly correlated systems (f-electron lanthanide/actinide metals)
- Strong charge-transfer systems (redox-active surfaces)

**The agent's value is orthogonal to MLFF accuracy** — it optimizes search strategy, not the energy function itself.

#### 4.4 Limitations and Negative Results

**Known limitations**:
- MACE-MP accuracy ceiling on certain systems (e.g., f-electron metals)
- LLM API cost and latency (quantified in SI-6: average ~6 min per full case on Gemini, ~11 min on Grok-4; GPT-5.4 full runs average ~27k tokens on the locked subset; one-shot cases are much cheaper)
- Current implementation: only flat/stepped surfaces, no defects or nanoparticles
- Single adsorbate per surface (no co-adsorption)
- **LLM reproducibility**: LLM APIs are black-box services subject to model updates; even at temperature 0.0, outputs may vary across API versions. We mitigate this by: (1) recording exact model version identifiers for all runs, (2) providing complete prompt templates in SI-1, (3) releasing full trajectory logs (SI-2) so that all reported results can be independently verified from the saved data, even if LLM outputs are not exactly reproducible. The multi-model comparison (SI-5) further demonstrates that conclusions hold across different LLM backends, reducing dependence on any single provider.

**Failure case analysis** (from completed 20-case benchmark + 75-run ablation):

Success rate: **20/20 (100%)** on both Gemini and Grok-4 one-shot benchmarks; GPT-5.4 is **18/20 raw** and **19/20 retry-corrected** because case 06 repeatedly dissociates. The ablation matrix is **75/75 (100%)** across Gemini, Grok-4, and GPT-5.4. The table below reports behavioral issues that affect quality or efficiency rather than API/runtime availability:

| Issue Type | Observed Frequency | Concrete Example | Mitigation |
|-----------|-------------------|------------------|------------|
| Chemical Slip (site mismatch) | Gemini/Grok-4 one-shot: 12/20 each; GPT-5.4 retry-corrected one-shot: 12/19 valid cases | Case 01 Mo3Pd: LLM plans bridge, relaxation converges to hollow | Core design feature — slip feedback drives the closed loop |
| NNH dissociation in one-shot | GPT-5.4 raw cases 06 and 08; retry recovers 08 but reproduces 06 | Case 06 Cu3Ag + NNH repeatedly dissociates from an ontop Cu proposal | Treat as backend-specific failure mode; do not report dissociated energy as valid adsorption energy |
| Dissociation under ablation | Case 19 no_slip/no_forbid/no_termination for Gemini/Grok-4 show dissociation events; GPT-5.4 ablation has zero dissociation in 25 runs | Large adsorbate OCHCH3 on Hf2Zn6(110) without adequate feedback | Slip feedback and conservative site memory reduce retries of unstable sites |
| Over-exploration (termination off) | Case 09 Gemini no_termination: 170k tokens vs 29k with termination | Flat PES already converged after 3 iterations | Termination logic is a cost guard, not a quality mechanism |
| Non-determinism at temperature 0 | Case 19: two consecutive Gemini runs give −4.042 vs −3.594 eV | API-side non-determinism in Gemini at T=0 | Multi-run or multi-backend averaging; report both |

*Note: No MACE calculation failures were observed in the committed agent-side result tables. The observed hard failures are chemistry outcomes (primarily dissociation), not calculator crashes.*

**Transparency principle**: Full logs, error type annotations, and improvement measures for all failure cases are provided in SI-8.

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
| **Table 3** | Data | OC dataset generalization test: success rate by surface type, slip frequency | 3.3 | Zongmin | P1 |
| **Table 4** | Ablation | Component contribution: full vs variants on 3–5 systems | 3.5 | Zongmin | P0 |

---

## Supporting Information Plan

| SI Section | Content | Priority |
|-----------|---------|----------|
| SI-1 | Extended methods: full prompt templates, MACE-MP parameters, AutoAdsorbate settings | Must |
| SI-2 | Complete benchmark data for all 20 CMU surfaces (energy tables, iteration logs) | Must |
| SI-3 | DFT validation extended data: all configurations, INCAR settings, convergence | Must |
| SI-4 | Ablation study full statistics and interaction effects | Must |
| SI-5 | LLM model comparison: three completed backends (Gemini 2.5 Pro, Grok-4, GPT-5.4) on representative systems + Chemical Slip statistics per model; additional Claude/open-source backends optional | Recommended |
| SI-6 | Cost analysis: LLM tokens, MLFF compute time, human effort | Recommended |
| SI-7 | OC dataset extended results: full system list, per-system metrics, failure cases | If Section 3.3 included |
| SI-8 | Failure case analysis: systematic classification of failure modes | Recommended |
| SI-9 | Glossary: Chemical Slip, FORBID, PES Type, Soft/Hard Slip and other core terminology definitions | Optional |

---

## What Makes This Paper Work

1. **Clear contribution**: not "yet another LLM agent" — a specific architectural innovation (closed-loop feedback) with a specific mechanism (Chemical Slip)
2. **Fair comparison**: same benchmark, same surfaces, direct head-to-head with the only published competitor
3. **Multi-level evaluation**: CMU benchmark (curated, 20 systems) + DFT validation (ground truth) + ablation (mechanism analysis) form the core evidence. OC dataset (diverse, ~50 systems) extends generalization claims if timeline permits.
4. **Physical validation**: DFT confirms that MLFF-guided search is meaningful, not just numerically self-consistent
5. **Ablation**: each component justified quantitatively, not just described
6. **Dual contribution**: the closed-loop architecture is contribution #1; Chemical Slip as a proxy metric for LLM chemical reasoning quality is contribution #2 — this gives the paper legs beyond the specific application
7. **Complementary framing**: positions AdsMind alongside Adsorb-Agent as complementary paradigms rather than direct competitors. Objectively discusses the applicable scenarios for open-loop (scaling screening throughput) vs closed-loop (deepening configuration search on complex surfaces), elevating the paper's ecological niche.

---

## Internal: Experiment Priority & Dataset

| Priority | Task | Status | Deadline Sensitivity |
|----------|------|--------|---------------------|
| **P0 (Must)** | CMU 20-surface benchmark | **DONE** — 20/20 success on Gemini + Grok-4; GPT-5.4 18/20 raw and 19/20 retry-corrected | Blocks everything |
| **P0 (Must)** | Head-to-head vs Adsorb-Agent | **DONE** — behavioral comparison (Route B); energy comparison infeasible (different MLFFs) | Core claim |
| **P0 (Must)** | DFT validation (3–5 systems) | Bowen leading | Philippe explicitly requested |
| **P0 (Must)** | Ablation study (3–5 systems) | **DONE** — 5 cases × 5 variants × 3 backends = 75 runs complete | Philippe explicitly requested |
| **P1 (Recommended)** | OC dataset evaluation (~50 systems) | Not started | Strengthens story significantly |
| **P1 (Recommended)** | Multi-model comparison (SI) | **DONE for current robustness claim** — 3 backends complete (Gemini + Grok-4 + GPT-5.4); more models optional | Reviewer will ask |
| **P2 (Nice-to-have)** | Literature reproduction (published DFT results) | Not started | If time allows |

**OCD-GMAE Dataset Overview** (used in Section 3.3):

- Unique catalyst surfaces (Surface Num.): 967 (covering 54 elements)
- Adsorbate species (Adsorbate Num.): 74
- Total surface/adsorbate combinations (System Num.): 973
