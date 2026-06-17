# Paper Artifact Archive Manifest

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
