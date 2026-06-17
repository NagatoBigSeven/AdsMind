# Contributing to AdsMind

Thanks for helping make AdsMind better. This project combines software,
scientific workflows, and curated benchmark data, so small, well-scoped changes
are easiest to review.

## Development Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run checks before opening a pull request:

```bash
python -m ruff check adsmind tests streamlit_app.py research
python -m compileall adsmind tests streamlit_app.py research
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Pull Request Guidelines

- Keep changes focused on one behavior, dataset update, or documentation topic.
- Include tests for agent logic, parsers, reporting, and reproducibility scripts
  when behavior changes.
- Document scientific protocol changes, including force-field settings,
  relaxation settings, seeds, and benchmark manifests.
- Do not commit API keys, provider credentials, private workstation paths, raw
  logs, or local recovery notes.
- Put large generated artifacts in release archives instead of normal Git
  history. See `paper-artifacts/MANIFEST.md`.

## Data and Results Policy

Curated public inputs belong under `datasets/`. Paper-facing summaries belong
under `research/results/` and should be documented in
`research/results/README.md`. Raw per-run payloads, logs, temporary structures,
and generated trajectories should remain ignored unless they are intentionally
promoted as release artifacts.

## Reporting Security Issues

Please do not open public issues for credential leaks, dependency vulnerabilities,
or other sensitive security reports. Follow [SECURITY.md](SECURITY.md).

