# OCD62 overlap12 Summaries

Reproducibility summaries for the 12 OCD62 cases repeated across independent
runs. This is not a separate benchmark dataset.

- `reproducibility_n2.csv`: N=2 paired reproducibility table.
- `reproducibility_n2.md`: N=2 human-readable report.
- `grok_ocd16_outlier_diagnosis.md`: diagnosis of the Grok OCD16 numerical
  collapse.
- `grok_ocd16_outlier_patch.csv`: summary-layer patch record for that outlier.

RUN3 outputs are generated only after the remote run lands:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```
