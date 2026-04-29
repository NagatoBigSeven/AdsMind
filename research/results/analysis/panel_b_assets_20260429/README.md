# Panel B Structure Assets 2026-04-29

Purpose: visual素材包 for the dataset/coverage panel.

Source convention:

- CMU20 thumbnails use GPT-5.4 Full relaxed structures from `openai_gpt54_ablation_v1/full` plus `cmu_extra5_openai_gpt54_ablation_v1/full`.
- OCD-GMAE thumbnails use GPT-5.4 Full relaxed structures from `ocd_gmae_rep50_openai_gpt54_full_v1/full`.
- Force field/checkpoint label for these rendered structures: MACE-MP-0 small.
- Individual PNGs use transparent backgrounds.
- Contact sheets are white-background previews for quick review; use individual PNGs for figure assembly.

Contents:

- `cmu20/`: 20 CMU benchmark thumbnails.
- `ocd_rep50_all/`: all 50 OCD-GMAE rep50 thumbnails.
- `ocd_rep50_selected/`: 20 non-CMU-selected OCD-GMAE thumbnails for Panel B coverage.
- `contact_sheets/`: preview sheets.
- `manifest.csv`: source/result path and metadata for every rendered asset.
- `panel_b_assets_20260429.zip`: zip archive for WeChat/group handoff.

Caveat:

These are visualization assets from AdsMind relaxed structures, not DFT validation snapshots. Use Bowen's VASP snapshots separately when discussing DFT/PBE validation.
