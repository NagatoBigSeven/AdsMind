# AdsMind Paper Artifact Manifest

The GitHub repository keeps software, documentation, examples, reproduction
scripts, and curated paper-facing summary tables. The external artifact bundle
is for raw or bulky material that should remain outside the main repository.

## Bundle Name

```text
adsmind-paper-artifacts-v0.1.0.zip
```

## Recommended Layout

```text
adsmind-paper-artifacts-v0.1.0/
  README.md
  checksums.sha256
  git_commit.txt
  environment/
    pyproject.toml
    python-version.txt
    package-lock-notes.md
  configs/
    frozen_configs/
    manifests/
  results/
    curated/
    raw_runs/
  trajectories/
    agent_logs/
    relaxed_structures/
  figures/
    source_data/
    rendered/
  structures/
    benchmark_slabs/
    generated_ocd_gmae_slabs/
```

## Main-Repository Content

Keep these in Git:

- `adsmind/` runtime package
- `docs/` user and developer documentation
- `examples/` small runnable examples
- `benchmark_slabs/` compact CMU benchmark structures
- `research/agent_eval/` reproduction scripts
- `research/results/` curated CSV/JSON/TEX tables used by the manuscript
- `paper/` manuscript source

## External Artifact Content

Put these in the release/Zenodo artifact if needed:

- per-run `result.json` payloads
- full agent logs and streamed reasoning traces
- generated trajectories (`*.traj`)
- large relaxed structures or candidate structure sets
- complete raw output directories
- rendered figure exports and source image bundles
- machine-readable environment snapshots

## Exclusions

Never include:

- API keys, cloud credential files, or provider tokens
- local shell profiles or workstation runbooks
- private machine paths that are not needed for reproduction
- `.git/`, `.venv/`, cache directories, or build directories

## Suggested Build Flow

Stage outside the repository:

```bash
ARTIFACT_ROOT=/tmp/adsmind-paper-artifacts-v0.1.0
rm -rf "$ARTIFACT_ROOT"
mkdir -p "$ARTIFACT_ROOT"

rsync -a research/results/ "$ARTIFACT_ROOT/results/curated/"
rsync -a research/agent_eval/configs/ "$ARTIFACT_ROOT/configs/frozen_configs/"
rsync -a research/agent_eval/manifests/ "$ARTIFACT_ROOT/configs/manifests/"
rsync -a benchmark_slabs/ "$ARTIFACT_ROOT/structures/benchmark_slabs/"

git rev-parse HEAD > "$ARTIFACT_ROOT/git_commit.txt"
python --version > "$ARTIFACT_ROOT/environment/python-version.txt"
cp pyproject.toml "$ARTIFACT_ROOT/environment/pyproject.toml"

find "$ARTIFACT_ROOT" -type f -print0 | sort -z | xargs -0 shasum -a 256 \
  > "$ARTIFACT_ROOT/checksums.sha256"

(cd /tmp && zip -r adsmind-paper-artifacts-v0.1.0.zip adsmind-paper-artifacts-v0.1.0)
```

Run the sensitive-content scan from `RELEASE.md` on the staged artifact before
uploading it.
