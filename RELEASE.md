# Release Checklist

Use this checklist before publishing AdsMind on GitHub or PyPI.

## 1. Build From a Clean Public Snapshot

Create the release from a repository that has no private Git history:

```bash
cd /path/to/workspace
rsync -a AdsMind/ AdsMind-public/ \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='.claude/' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='*.credentials.json' \
  --exclude='uv.lock' \
  --exclude='outputs/' \
  --exclude='build/' \
  --exclude='dist/' \
  --exclude='*.egg-info/' \
  --exclude='__pycache__/' \
  --exclude='.ruff_cache/' \
  --exclude='.pytest_cache/'
cd AdsMind-public
git init
```

Do not publish the historical development `.git` directory.

## 2. Final Content Scan

```bash
rg -n --no-ignore --hidden --glob '!.git/**' --glob '!.venv/**' \
  --glob '!uv.lock' \
  '/[U]sers/|/[d]ata/|BEGIN [A-Z ]*PRIVATE KEY|AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-' .

find . \( -path './.git' -o -path './.venv' \) -prune -o -type f -size +5M -print
```

Both commands should return no unexpected matches.

## 3. Runtime Checks

```bash
python -m pip install -e ".[dev,research]"
python -m compileall adsmind tests streamlit_app.py research
adsmind-preflight --ci
python -m unittest discover -s tests -p 'test_*.py' -v
```

## 4. Packaging Checks

```bash
python -m build --sdist --wheel
twine check dist/*
```

Inspect the wheel contents before upload:

```bash
python -m zipfile -l dist/adsmind-*.whl
```

The PyPI wheel should contain the runtime `adsmind/` package and metadata only; the
repository-only `research/` and `tests/` trees should not be packaged.

Confirm that the intended PyPI project name is still available immediately
before upload; package-name availability can change at any time.

## 5. Paper Artifacts

The main repository keeps curated summaries, tables, scripts, and small examples.
Large or raw paper artifacts should be staged outside the repository and uploaded
as `adsmind-paper-artifacts-v0.1.0.zip` to the matching GitHub release. Use the
layout described in `paper-artifacts/MANIFEST.md`, then upload the same zip to
Zenodo for a DOI before manuscript submission.

## 6. Publish

Tag the same commit used for the PyPI upload, attach the sdist/wheel to the
GitHub release, and include the commit hash in the release notes.
