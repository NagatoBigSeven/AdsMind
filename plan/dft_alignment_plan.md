# DFT Alignment and Iteration-Trajectory Analysis Plan

## Status as of 2026-04-27

This is a **current-stage plan**, not a final analysis plan. The DFT side is still incomplete and the current deliverable is an MVP handoff package for one system:

- Current complete-enough DFT spreadsheet column: `Mo3Pd_111_H` / CMU case 01 only.
- Current AdsMind MVP package:
  - `/Users/nagato/workspace/AdsMind/research/results/analysis/dft_iteration_alignment/case_01/`
- Current available AdsMind structures:
  - GPT-5.4: 4/4 iteration `.xyz` files and quick PNG snapshots.
  - Claude Sonnet 4.6: 4/4 iteration `.xyz` files and quick PNG snapshots.
  - Gemini 2.5 Pro: 5/5 iteration metadata, but no locked `.xyz` artifacts locally or remotely.
  - Grok-4: 5/5 iteration metadata, but no locked `.xyz` artifacts locally or remotely.
- Figure expectation: the eventual DFT/iteration figure should include all four LLM backends where possible, but the current MVP can only render GPT-5.4 and Claude from locked local artifacts.
- Pending remote visualization-only reruns:
  - Gemini 2.5 Pro: CMU case 01 structure-snapshot recovery run.
  - Grok-4: CMU case 01 structure-snapshot recovery run.
  These reruns are intended only to recover case-01 structure snapshots for the four-model figure. They must not replace the locked ablation statistics or be pooled into formal benchmark summaries.
- Current available DFT reference values:
  - `E_slab`, `E_slab_ads`, `E_H`, `E_ads`, and `Delta_G` transcribed from Bowen's current `VASP.xls` column B.
- Current missing DFT inputs:
  - final `CONTCAR`;
  - preferably `OUTCAR` or `vasprun.xml`;
  - full calculation settings;
  - publication-ready snapshots.

The plan must be rerun and tightened after Bowen provides the DFT final structure package. The current package is suitable for PI/Lou/Bowen figure-concept alignment, not for manuscript-grade DFT claims.

Remote visualization reruns should be checked only after the Overleaf revision pass or after a sufficient waiting interval; do not keep active monitoring as a blocking task.

## Goal

Build a rigorous DFT-alignment workflow for the application/result figures. The purpose is not to claim that MACE-MP-0 small absolute adsorption energies equal DFT/PBE energies. The purpose is to compare AdsMind's per-iteration structural trajectory with a DFT reference final state, so that the manuscript can show interpretable closed-loop behavior:

- Some backends may start close to the DFT reference but drift away.
- Some backends may start poorly but recover through feedback.
- Some trajectories may show physically meaningful migration, slip, or dissociation.
- AdsMind's value is not only the final scalar energy, but also an inspectable sequence of hypotheses, relaxed structures, and feedback signals.

This supports the planned application/result panels, especially the DFT application panel and the iteration-trajectory panel.

## PI Intent Check

The PI's request is figure- and insight-driven, not a request for a full DFT benchmarking campaign before any deliverable exists. The near-term objective is to produce a concrete comparison for one complete system, then use that template to expand when Bowen's data arrive.

The plan must therefore satisfy two levels:

1. **MVP for immediate discussion.** For `Mo3Pd_111_H` / CMU case 01, show AdsMind's per-iteration hypothesis, relaxed conformer, and MACE energy curve against Bowen's DFT/PBE final reference. This gives PI/Lou/Bowen a concrete figure concept before every DFT file is perfect.
2. **Full analysis for manuscript/SI.** Once Bowen provides final structures and calculation metadata, compute structural alignment metrics and produce SI-grade tables.

The central scientific question is whether the iteration trajectory reveals a pattern: memory-like first guesses, reasoning-driven correction, degradation after a good first guess, migration toward the DFT reference, or failure despite feedback. In internal discussion the DFT/PBE result may be treated as the comparison target; in the manuscript, the safer wording is "DFT/PBE reference final state" rather than an unconditional "ground truth."

## Current Known Facts

- Bowen's current `VASP.xls` contains one reliable complete first-reference column for `Mo3Pd_111_H`.
- `Mo3Pd_111_H` corresponds to CMU case 01 in `research/agent_eval/manifests/cmu_manifest.csv`.
- The reliable current DFT/PBE values from column B are:
  - `E_slab = -568.24731439 eV`
  - `E_slab_ads = -572.73088949 eV`
  - `E_H = -3.361475545 eV`
  - `E_ads = -1.122099555 eV`
  - `Delta_G = -0.988283055 eV`
- Columns D/E in the sheet have no headers and Bowen clarified that they are draft/convergence/transition-state-related data. They must not be used as final DFT reference data.
- Pt/OH columns are not ready for final use because some reference terms are incomplete or inconsistent.
- The local DFT-alignment preparation package already exists for CMU case 01:
  - `/Users/nagato/workspace/AdsMind/research/results/analysis/dft_iteration_alignment/case_01/`
- That package includes per-iteration metadata and copied structure artifacts where available. GPT-5.4 and Claude Sonnet 4.6 have local `.xyz` structures; Gemini and Grok currently have metadata/energies but not local `.xyz` artifacts.

## Data Required From Bowen

For every DFT-alignment system, ask Bowen for a complete, unambiguous data package. To match the PI's schedule, separate the minimum package needed for the first figure draft from the full reproducibility package.

### Minimum package for first figure draft

1. System name and state label, e.g. `Mo3Pd_111_H`, final state vs TS vs draft.
2. DFT optimized final structure, preferably `CONTCAR`.
3. DFT adsorption energy or the component energies needed to compute it.
4. Transparent-background snapshots with consistent view/color for initial and final states; TS snapshot only if a formal TS exists.

### Full package for manuscript/SI

1. System identity:
   - system name, e.g. `Mo3Pd_111_H`
   - AdsMind/CMU case ID if known
   - whether the structure is an initial state, final optimized state, transition state, or intermediate draft

2. DFT structures:
   - initial adsorption structure: `POSCAR` or initial `CONTCAR`
   - optimized final structure: final `CONTCAR`, preferably with `OUTCAR` or `vasprun.xml`
   - transition-state or NEB structure only if a formal TS/NEB calculation was actually performed

3. DFT energies:
   - `E_slab`
   - `E_adsorbate`
   - `E_slab+ads`
   - `E_ads`
   - `G_correction`, if available
   - `Delta_G`, if available

4. DFT settings:
   - functional
   - ENCUT
   - KPOINTS
   - spin setting
   - fixed atoms / slab constraints
   - whether D3, Hubbard U, dipole correction, or other corrections are used

5. Figure assets:
   - initial snapshot
   - final snapshot
   - TS snapshot only if a formal TS exists
   - transparent background
   - consistent camera angle
   - consistent atom colors and sizes

## AdsMind Data To Extract

For each selected case and backend, extract the following from AdsMind run artifacts:

- backend name
- variant, normally Full for DFT alignment
- iteration index
- structured JSON hypothesis proposed by the planner
- short human-readable summary of the planner's intended adsorption motif
- planned site type
- planned surface symbols / atom IDs
- adsorbate binding atom indices
- relaxed actual site type
- relaxed actual surface coordination
- MACE adsorption energy
- whether this iteration updated the running best energy/configuration
- slip flag
- site mismatch flag
- dissociation/rearrangement flags
- valid relaxed configuration status
- relaxed `.xyz` structure, where available
- final selected best configuration

The first template case should remain CMU case 01 (`Mo3Pd_111_H`) because it is the only currently reliable DFT reference.

Prepare this data in a form that can be handed to Lou/Bowen directly: one trajectory table, one energy-curve CSV, and selected `.xyz`/snapshot files for the iterations that best illustrate migration or failure. The handoff should preserve every iteration in the table even if the figure only visualizes a subset; otherwise the trajectory can look cherry-picked.

## Analysis Workflow

### 1. Data cleaning

- Accept only DFT columns with explicit headers and confirmed final-state meaning.
- Reject draft, convergence, or unlabeled columns from final analysis.
- Keep TS data separate from final-state data.
- Standardize all energies to eV.
- Record whether `Delta_G` includes thermal correction at 298.15 K and 1 atm.

### 2. Structure alignment

- Align AdsMind relaxed structures to the DFT final structure using the slab atoms as the reference frame.
- Avoid using whole-system RMSD as the only metric, because adsorbate migration can dominate the number.
- Focus on the adsorbate anchor atom and its local surface coordination.

### 3. Geometry metrics

For each iteration:

- planned site type vs AdsMind relaxed actual site type
- AdsMind relaxed actual site type vs DFT final site type
- planned surface symbols vs realized surface symbols
- realized surface atoms vs DFT surface atoms
- adsorbate-anchor height above the surface
- adsorbate-anchor lateral displacement relative to DFT final site
- key adsorbate-surface bond distances
- adsorbate RMSD after slab alignment
- whether slip/dissociation/rearrangement occurred

### 4. Energy-trajectory metrics

- Plot MACE adsorption energy per iteration.
- Mark the running best configuration updates.
- Mark failed or invalid iterations separately.
- The main curve should be the AdsMind/MACE energy trajectory because this is what the agent observes.
- Bowen's DFT/PBE final energy may be shown as a clearly labeled reference endpoint or annotation, but not interpreted as being on the same force-field scale as MACE-MP-0 small unless the caption explicitly states the mismatch in energy models.
- Use DFT primarily as the PBE-level structural reference endpoint, not as an absolute calibration of MACE-MP-0 small energies.

### 4a. First figure draft requirements

The first figure draft should be simple and interpretable:

- show iteration number explicitly, e.g. attempt 1--5
- show the relaxed candidate structure or a consistent snapshot for each displayed iteration
- label planned site and relaxed actual site when space allows
- mark slip/dissociation/invalid iterations with a visible diagnostic marker
- show MACE adsorption energy as the agent-observed trajectory
- mark the best-so-far update points
- place the DFT/PBE final structure as the reference endpoint, not as another MACE trajectory point
- use arrows only when they represent actual observed structural migration, not an invented schematic path

This first draft is for PI/Lou/Bowen alignment. It does not need every SI-grade metric before the visual concept is checked.

### 5. Behavioral classification

Classify each backend trajectory into interpretable categories:

- first-shot close and stable
- first-shot close but later degraded
- initially wrong but recovered through feedback
- repeated slip but eventual recovery
- natural failure through dissociation or invalid relaxed structure
- no meaningful convergence

These categories are the scientific content the DFT alignment can add to the paper.

## Outputs

The final DFT-alignment deliverable should include:

1. `dft_reference_table.csv`
2. `agent_iteration_trajectory.csv`
3. `structure_alignment_metrics.csv`
4. aligned `.xyz` structures
5. snapshots for the DFT final state
6. snapshots for selected AdsMind iteration states
7. Panel D draft: DFT reference/application comparison
8. Panel E draft: AdsMind iteration trajectory
9. SI table: per-iteration planned site, actual site, DFT reference site, energy, status
10. one-paragraph main-text interpretation
11. Lou/Bowen handoff folder containing selected structures and snapshots for figure production
12. short internal note classifying each backend trajectory as memory-like, reasoning/recovery-like, degraded-after-good-start, or failed

The current MVP package already includes:

- `MVP_HANDOFF.md`;
- `agent_iteration_trajectory.csv`;
- `agent_run_summary.csv`;
- `energy_curve.csv`;
- `energy_curve.svg`;
- `snapshot_contact_sheet.png`;
- `structures/GPT_5.4/`;
- `structures/Claude_Sonnet_4.6/`;
- quick `snapshots/` for GPT-5.4 and Claude;
- `FILE_MANIFEST.md`.

The current MVP package does **not** include formal `structure_alignment_metrics.csv`, because that requires Bowen's final DFT structure.

## Manuscript Interpretation Rules

- Do not claim MACE-MP-0 small absolute adsorption energies are DFT-accurate.
- Do not call an intermediate AdsMind relaxed structure a transition state unless Bowen provides a formal DFT TS/NEB result.
- Do not treat MACE-MP-0 large as DFT validation; it is only a force-field sensitivity check.
- Do not use Bowen's unlabeled D/E draft columns.
- Do not replace locked benchmark statistics with visualization-only reruns.
- Do not claim AdsMind is always energetically deeper than brute-force methods.
- In manuscript wording, prefer "DFT/PBE reference final state" over "ground truth" unless PI explicitly decides otherwise.
- Do not omit failed or worse iterations from the trajectory table; they are central to the memory-vs-reasoning insight.

## Execution Order

1. Keep CMU case 01 as the first template system.
2. Use the current MVP handoff package for near-term PI/Lou/Bowen alignment.
3. Confirm Bowen's minimum DFT package for case 01: final structure, final energy components, and initial/final snapshots.
4. Produce a first case 01 visual draft: iteration snapshots plus MACE energy curve, with Bowen's DFT final state shown as the structural reference.
5. Align GPT-5.4 and Claude trajectories first because local structures already exist.
6. If four-backend visualization is required, rerun Gemini/Grok case 01 only in a separate visualization-only directory; do not replace locked benchmark statistics.
7. Generate an SI-grade case 01 alignment table after Bowen provides the full DFT package.
8. Ask PI/Bowen to validate the interpretation.
9. Expand to additional systems only after the case 01 template is approved.
10. Rebuild this DFT plan after new DFT systems arrive, because the current plan is intentionally scoped to the first MVP example.

## Open Risks

- Bowen's current DFT spreadsheet is incomplete beyond the first case.
- Some AdsMind backends have missing local structure artifacts.
- DFT and MACE use different energy functions; absolute energy comparisons are not valid without careful framing.
- TS terminology is high-risk and should be avoided unless a formal TS calculation exists.
- The final panel should emphasize structural trajectory and feedback behavior, not absolute MACE-vs-DFT energy agreement.
- A too-heavy analysis pipeline could miss the PI's immediate need for a concrete figure draft. The first deliverable should therefore be an MVP trajectory demo, followed by rigorous SI metrics.
