# Lou/Bowen MVP Handoff: CMU case 01

System: `Mo3Pd_111_H` / CMU case 01.

Use this package for a first figure discussion only. The DFT/PBE final structure from Bowen is still needed before manuscript-grade structural alignment can be claimed.

## Files to use now

- `agent_iteration_trajectory.csv`: complete per-attempt table, including planner JSON and analyzer diagnostics.
- `energy_curve.csv`: compact plotting table for the MACE-small energy trajectory.
- `energy_curve.svg`: quick visual draft of the agent-observed MACE energy curve.
- `agent_run_summary.csv`: backend-level summary and trajectory classification inputs.
- `structures/`: currently copied relaxed `.xyz` files where artifacts exist.
- `snapshots/`: quick transparent PNG renders generated from available `.xyz` files, if present.
- `snapshot_contact_sheet.png`: quick contact sheet for discussion, if present.
- `FILE_MANIFEST.md`: generated file list for handoff auditing, if present.
- `dft_reference_template.csv`: values transcribed from Bowen's current `VASP.xls` column B plus fields still needed.

## Provisional trajectory pattern before DFT structural alignment

These labels are internal reading aids based only on the AdsMind/MACE trajectory. They should not be used as manuscript conclusions until Bowen's DFT/PBE final structure has been aligned.

- gpt54_mace_mp0_small: memory-like-with-degenerate-refinement; iterations=4, best iteration=4, best MACE E=-3.627323865890503 eV, improvement vs first=0.00372314453125 eV.
- claude_sonnet46_mace_mp0_small: reasoning-recovery-like; iterations=4, best iteration=4, best MACE E=-3.630131483078003 eV, improvement vs first=0.0728759765625 eV.
- gemini25pro_mace_mp0_small: memory-like-with-degenerate-refinement; iterations=5, best iteration=3, best MACE E=-3.6317179203033447 eV, improvement vs first=0.00054931640625 eV.
- grok4_mace_mp0_small: memory-like-with-degenerate-refinement; iterations=5, best iteration=3, best MACE E=-3.6317179203033447 eV, improvement vs first=0.0006103515625 eV.

## Local handoff artifact status

- Copied relaxed structures in this handoff package: 8.
- Quick PNG snapshots in this handoff package: 8.
- Gemini and Grok are represented in the summary tables; this local DFT-alignment package does not currently include their per-iteration `.xyz` copies.

## Figure cautions

- Plot MACE energy as the agent-observed trajectory.
- Show Bowen's DFT/PBE final structure as a reference endpoint, not as a MACE-energy point.
- Keep failed, worse, or slipped iterations in the table even if the figure only labels selected frames.
- Do not call any AdsMind intermediate a transition state unless Bowen supplies a formal DFT TS/NEB result.
