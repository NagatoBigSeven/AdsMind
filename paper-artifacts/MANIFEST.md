# Paper Artifact Archive Manifest

> **Status (2026-06):** The release archive described below is **not yet
> published**. Everything cited in the paper's Data Availability statement —
> benchmark manifests, frozen run configurations, reproduction scripts,
> four-backend by five-variant summary tables, per-agent ablations, Heuristic
> and Adsorb-Agent baseline comparisons, and the N=3 reproducibility data — is
> already in the committed repository tree (`datasets/`, `research/`). The raw
> run payloads listed below (trajectories, per-run artifacts, logs) will be
> attached to the release when published, and are available from the sole
> first author on request in the meantime.

Large raw payloads should be distributed as a release archive rather than
committed directly. The intended archive name for the first public release is:

```text
adsmind-paper-artifacts-v0.1.0.zip
```

Recommended archive layout:

```text
adsmind-paper-artifacts-v0.1.0/
  README.md
  checksums.txt
  results/
    basic_experiments/
    advanced_experiments/
  trajectories/
  figures/
  provenance/
```

Minimum metadata to include:

- AdsMind release version and commit hash.
- Python version, platform, calculator backend, and force-field settings.
- LLM backend/model labels without API keys or provider credentials.
- Dataset manifest paths and checksums for promoted inputs.
- Clear notes explaining which files reproduce each paper table or figure.

Attach the zip to the matching GitHub release.
