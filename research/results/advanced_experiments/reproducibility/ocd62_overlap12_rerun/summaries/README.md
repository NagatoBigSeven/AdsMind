# OCD62 overlap12 Summaries

Reproducibility summaries for the 12 OCD62 cases repeated across independent
runs. This is not a separate benchmark dataset.

- `reproducibility_n2.csv`: N=2 paired reproducibility table.
- `reproducibility_n2.md`: N=2 human-readable report.
- `reproducibility_n3.csv`: N=3 repeated-run reproducibility table.
- `reproducibility_n3.md`: N=3 human-readable report.
- `reproducibility_n4.csv`: N=4 repeated-run reproducibility table, using
  complete run1 through run4 data.
- `reproducibility_n4.md`: N=4 human-readable report.
- `run5_partial_manifest.csv`: audit record for partial run5 data. Run5 Grok
  is excluded because the remote copy contains external OpenRouter 402
  credit/billing failures.
- `grok_ocd16_outlier_diagnosis.md`: diagnosis of the Grok OCD16 numerical
  collapse.
- `grok_ocd16_outlier_patch.csv`: summary-layer patch record for that outlier.

Refresh the N=3 and N=4 summaries from the run directories with:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3 --write-n4
```
