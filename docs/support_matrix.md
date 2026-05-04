# Support Matrix

This document distinguishes between platforms that are actively exercised in
automation and platforms that are expected to work but are not continuously
validated.

## Python Versions

| Version | Status | Evidence |
|--------|--------|---------|
| 3.10 | CI-tested | GitHub Actions unit-test job |
| 3.11 | CI-tested | GitHub Actions unit-test job |
| 3.12+ | Unsupported for packaged installs | Current MACE/PyTorch baseline is pinned to Python 3.10/3.11 |

## Operating Systems

| Platform | Status | Notes |
|---------|--------|------|
| Linux CPU | Supported | CI baseline and recommended default |
| macOS CPU / Apple Silicon | Supported | Covered by the workflow matrix plus local smoke validation |
| Linux CUDA | Supported with caveats | Requires a working CUDA/PyTorch/MACE stack on the host |
| Windows | Best effort | No active validation or packaging guarantees |

## LLM Backends

| Backend | Status | Validation Level |
|--------|--------|------------------|
| Anthropic | Core-hosted | Config and factory tests |
| OpenAI | Core-hosted | Config and factory tests |
| OpenRouter | Core | Config and factory tests, production default |
| Ollama | Core | Config and factory tests; requires local daemon |
| HuggingFace | Experimental-local | Factory tests plus cache-key regression test; model availability depends on host stack |

## Calculator Backends

| Backend | Status | Notes |
|--------|--------|------|
| MACE | Core | Default and only fully wired calculator path |
| OpenMD | Stub | Placeholder only; not feature-complete |

## Validation Scope

- `python -m unittest discover -s tests -p 'test_*.py' -v` is the required regression baseline.
- `python -m compileall adsmind tests streamlit_app.py research` is the required import/compile smoke baseline.
- `adsmind-preflight --ci` is the required install/runtime sanity baseline.
- `python -m build --sdist --wheel` and `twine check dist/*` are the required packaging checks before PyPI upload.
- Streamlit, remote APIs, and heavy relaxation runs are validated as runtime paths, but not exercised in CI to avoid network and hardware coupling.
