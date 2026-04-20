# Contributing

Contributions are welcome. This repository currently uses a lightweight Python
toolchain instead of the original template defaults.

## Setup

```bash
uv pip install -e ".[dev]"
```

## Checks Before Opening a PR

```bash
python -m compileall adsmind tests streamlit_app.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

For release-facing changes, also run:

```bash
python -m build --sdist --wheel
twine check dist/*
```

## Scope

- Runtime code lives under `adsmind/`
- Tests live under `tests/`
- Research and manuscript assets live under `research/` and `paper/`

## Expectations

- Keep changes focused and reversible.
- Add or update tests when behavior changes.
- Prefer `logging` over ad-hoc `print()` in reusable library code.
- Avoid mixing research-only scripts into the runtime path.
- Never commit API keys, cloud credential files, local machine paths, or
  private workstation runbooks.
