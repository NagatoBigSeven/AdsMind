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
- `reproducibility_n5.csv`: N=5 repeated-run reproducibility table, using
  complete run1 through run5 data after the run5 Grok credit-recovery rerun.
- `reproducibility_n5.md`: N=5 human-readable report.
- `run2/grok4_mace_mp0_small/one_shot/006/result.external_failure_openrouter_429.json`:
  preserved audit copy of the original OpenRouter monthly-credit failure. The
  official `result.json` for that case is the same-protocol repair run and is
  classified as an internal dissociation/no-molecular-best failure.
- `run5_manifest.csv`: audit record for accepted run5 data. All four backends
  have been pulled; no external credit/billing failures remain in the accepted
  run5 directories.
- `../logs/run45/`: audited remote pull and recovery logs for the run4/run5
  ingestion, including the Grok run5 credit-recovery rerun.
- `grok_ocd16_outlier_diagnosis.md`: diagnosis of the Grok OCD16 numerical
  collapse.
- `grok_ocd16_outlier_patch.csv`: summary-layer patch record for that outlier.

Refresh the paired reproducibility summaries from the run directories with:

```bash
PYTHONPATH=. .venv/bin/python research/analysis/build_ocd62_summary.py
```
