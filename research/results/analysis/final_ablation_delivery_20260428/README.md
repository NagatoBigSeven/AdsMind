# Final Ablation Delivery 2026-04-28

This directory is the figure/writing delivery layer derived from `../clean_ablation_20260428/`.

Files:

- `plot_cmu20_delta_points.csv`: success-only CMU20 delta points for plotting.
- `plot_ocd24_delta_points.csv`: success-only OCD24 delta points for plotting.
- `plot_rep50_delta_points.csv`: success-only rep50 Full-vs-1-Shot delta points for plotting.
- `failure_audit.csv`: natural/external failure audit rows for annotations and SI.
- `figure_caption_notes.md`: caption and axis notes for Lou Yuyang.
- `ablation_insights_for_writing.md`: concise data interpretation for manuscript text.

Formal convention:

- `Delta E = E_variant - E_full`.
- Positive delta means variant/1-Shot is higher energy and less stable than Full.
- Delta distributions are success-only.
- Natural failures are reported separately in `failure_audit.csv`.
