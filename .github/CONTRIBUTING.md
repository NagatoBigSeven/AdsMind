# Contributing

Contributions are welcome. This repository currently uses a lightweight Python
toolchain instead of the original template defaults.

## Setup

```bash
uv pip install -e ".[dev]"
```

## Checks Before Opening a PR

```bash
python -m compileall src tests streamlit_app.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Scope

- Runtime code lives under `src/`
- Tests live under `tests/`
- Research and manuscript assets live under `research/` and `AdsMind/`

## Expectations

- Keep changes focused and reversible.
- Add or update tests when behavior changes.
- Prefer `logging` over ad-hoc `print()` in reusable library code.
- Avoid mixing research-only scripts into the runtime path.
