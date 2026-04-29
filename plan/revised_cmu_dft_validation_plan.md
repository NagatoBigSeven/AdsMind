# Revised CMU / DFT Validation Plan

## Current Status

This is a current-stage plan for the possible "revised CMU benchmark" angle. It should not be treated as a completed result until Bowen's DFT source files and calculation settings are available.

The team discussion has clarified three facts:

- The CMU/CatalystAIgent paper provides a 20-case surface task set and reported adsorption energies, but it does not provide a complete structure-resolved benchmark with final adsorption geometries.
- AdsMind now has relaxed final structures, energies, and metadata for the CMU20 cases.
- Bowen's DFT/PBE results suggest that at least selected CMU-reported energy records may require structure-level validation, but this must be handled cautiously and only after reference-state definitions are aligned.

The near-term safe framing is:

> AdsMind extends the CMU benchmark from energy-only task reports to a structure-resolved adsorption benchmark by providing relaxed configurations, energies, and traceable metadata.

Do **not** write that "CMU is wrong" in the manuscript. The defensible manuscript language is that selected reported records may require structure-level validation, and that AdsMind provides revised/validated configurations where DFT/PBE support is available.

## Distinction From The DFT Trajectory Plan

This file is about benchmark validation and possible revised CMU records.

The existing `plan/dft_alignment_plan.md` is about per-iteration agent trajectory analysis, memory/reasoning behavior, and figure panels using iteration snapshots.

These are related but not identical:

- DFT trajectory analysis asks: how does AdsMind move over iterations toward or away from a DFT/PBE reference structure?
- Revised CMU validation asks: can we provide structure-resolved, DFT-supported records that improve upon the original CMU energy-only reports?

## Required Inputs Before Any Manuscript Claim

For each candidate revised CMU case, we need a complete enough DFT package from Bowen:

1. System identity:
   - CMU case ID
   - surface formula and Miller index
   - adsorbate identity
   - whether the record is final state, transition state, intermediate, or draft

2. DFT structures:
   - initial adsorption structure, preferably POSCAR
   - final optimized structure, preferably CONTCAR
   - OUTCAR or vasprun.xml where available
   - TS/NEB structure only if it is a formal TS/NEB calculation

3. DFT energy definition:
   - E_slab
   - E_adsorbate
   - E_slab+ads
   - E_ads
   - whether E_ads uses H atom, 1/2 H2, OH, NNH, or other reference
   - G_correction and Delta_G if present
   - temperature and pressure for thermodynamic correction

4. DFT calculation settings:
   - functional
   - ENCUT
   - KPOINTS
   - spin setting
   - fixed atoms / slab constraints
   - dispersion, Hubbard U, dipole correction, or other corrections if used

5. Literature support where a discrepancy is large:
   - at least one relevant PBE or comparable DFT literature value
   - note the reference convention and surface/coverage

## Immediate Candidate Cases

### Case 01: Mo3Pd(111)-H

Reason to start here:

- Bowen's current spreadsheet column B is the most complete.
- It maps cleanly to CMU case 01.
- AdsMind has per-iteration and final relaxed structures.

Current caution:

- Bowen still needs to provide the final structure files and full settings before manuscript-grade claims.

### Pt(111)-related cases

Reason to investigate:

- Bowen reported that Pt(111) differs from the CMU-reported value by roughly 3 eV.
- Bowen also indicated that literature values support his PBE result more closely than the CMU-reported value.

Current caution:

- This could be a real benchmark inconsistency, but it could also be a reference-state mismatch, coverage mismatch, adsorbate identity mismatch, or thermodynamic-correction mismatch.
- Do not mention this as a CMU error until the energy definition and literature comparison are aligned.

## Validation Table To Build

Once Bowen's files arrive, build a table with one row per validated candidate:

| field | meaning |
| --- | --- |
| case_id | CMU case ID |
| system | surface + adsorbate |
| CMU_reported_energy_eV | value from original CMU table |
| CMU_energy_definition | if recoverable from paper/SI |
| AdsMind_MACE_energy_eV | AdsMind relaxed energy under MACE-MP-0 small |
| AdsMind_site | realized relaxed adsorption site |
| DFT_PBE_E_ads_eV | Bowen's DFT/PBE adsorption energy |
| DFT_reference_definition | slab/adsorbate reference convention |
| Delta_CMU_vs_DFT_eV | CMU reported minus DFT/PBE, same convention only |
| Delta_AdsMind_vs_DFT_eV | AdsMind/MACE minus DFT/PBE, label as cross-model only |
| structure_agreement | whether AdsMind final site matches DFT final site |
| literature_support | citation/key note where available |
| verdict | validated / possible mismatch / unresolved |
| manuscript_use | main text / SI / internal only |

Important: only compute energy differences when the reference definitions match. If not, write `not comparable` rather than forcing a number.

## Figure / SI Use

Possible outputs after validation:

1. Main figure or inset:
   - show CMU task surface
   - show AdsMind relaxed configuration
   - show DFT/PBE final structure for selected case
   - annotate structure/site agreement rather than only energy agreement

2. SI table:
   - list the structure-resolved CMU20 AdsMind records
   - include file paths and metadata
   - include DFT validation rows only for cases with complete DFT packages

3. Data release statement:
   - state that the work provides relaxed AdsMind configurations and metadata for CMU20
   - state that selected records are cross-checked against DFT/PBE where available

## Manuscript Wording Rules

Safe wording:

- "structure-resolved extension of the CMU benchmark"
- "selected records were further compared against DFT/PBE calculations"
- "DFT/PBE comparison suggests that structure-level validation is important for interpreting reported adsorption energies"
- "we provide relaxed configurations and metadata to improve reproducibility"

Avoid:

- "CMU is wrong"
- "their dataset is bad"
- "AdsMind proves the original benchmark is incorrect" unless every reference convention has been matched and documented
- "ground truth" for MACE results
- energy-difference claims across MACE and DFT without clearly labeling them as cross-model comparisons

## Execution Order

1. Keep the Panel B asset pack separate from DFT validation. The Panel B images are AdsMind/MACE visual assets, not DFT validation results.
2. Wait for Bowen's source-file zip.
3. For each DFT candidate, parse and record structures, energies, and settings.
4. Reconstruct the energy convention and reject non-comparable rows.
5. Compare final adsorption site and local coordination between AdsMind and DFT.
6. Only then decide whether a case belongs in:
   - main text;
   - SI validation table;
   - internal-only notes.
7. After enough cases are validated, update the manuscript with cautious structure-resolved benchmark wording.

## Current Deliverables Already Prepared

- Panel B visual asset pack:
  - `research/results/analysis/panel_b_assets_20260429/panel_b_assets_20260429.zip`
- Panel B manifest:
  - `research/results/analysis/panel_b_assets_20260429/manifest.csv`
- Panel B handoff message:
  - `research/results/analysis/panel_b_assets_20260429/wechat_handoff_message.md`
- Generation script:
  - `research/agent_eval/render_panel_b_assets.py`

These are ready for Lou/PI figure work, but they should not be cited as DFT validation.
