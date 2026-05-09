"""Export sanitized per-run configuration sidecars for result directories.

The raw ``config.json`` files are useful for reproducibility, but they can also
contain credential-source fields or local paths.  This script writes a
``run_config.public.json`` next to each raw config with those fields redacted.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_RESULTS_ROOT = Path("research/results")
RAW_CONFIG_NAME = "config.json"
PUBLIC_CONFIG_NAME = "run_config.public.json"

SENSITIVE_KEY_RE = re.compile(
    r"(^|[_-])("
    r"api[_-]?key|api[_-]?key[_-]?source|secret|credential|password|"
    r"authorization|bearer[_-]?token|access[_-]?token|refresh[_-]?token|"
    r"id[_-]?token"
    r")([_-]|$)",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(sk-or-v1-[A-Za-z0-9]+|sk-proj-[A-Za-z0-9_-]+)"
)
ENV_ASSIGNMENT_RE = re.compile(
    r"((?:OPENROUTER|ANTHROPIC|OPENAI|GOOGLE)_API_KEY\s*=\s*.+)"
)
LOCAL_ABS_PATH_RE = re.compile(r"^(/Users/|/data/)")


def _sanitize(value: Any, path: tuple[str, ...], redacted: list[str]) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, child in value.items():
            child_path = (*path, str(key))
            if SENSITIVE_KEY_RE.search(str(key)):
                sanitized[key] = "<redacted>"
                redacted.append(".".join(child_path))
            else:
                sanitized[key] = _sanitize(child, child_path, redacted)
        return sanitized

    if isinstance(value, list):
        return [_sanitize(child, (*path, "[]"), redacted) for child in value]

    if isinstance(value, str):
        if SECRET_VALUE_RE.search(value) or ENV_ASSIGNMENT_RE.search(value):
            redacted.append(".".join(path))
            value = SECRET_VALUE_RE.sub("<redacted>", value)
            return ENV_ASSIGNMENT_RE.sub("<redacted>", value)
        if LOCAL_ABS_PATH_RE.match(value):
            redacted.append(".".join(path))
            return "<redacted-local-path>"
        return value

    return value


def export_one(raw_path: Path, *, dry_run: bool = False) -> bool:
    with raw_path.open() as handle:
        raw = json.load(handle)

    redacted: list[str] = []
    public = _sanitize(raw, (), redacted)
    public["_public_config"] = {
        "schema_version": 1,
        "source_file": RAW_CONFIG_NAME,
        "redacted_fields": sorted(set(redacted)),
    }

    output_path = raw_path.with_name(PUBLIC_CONFIG_NAME)
    text = json.dumps(public, indent=2, sort_keys=True) + "\n"
    if output_path.exists() and output_path.read_text() == text:
        return False
    if not dry_run:
        output_path.write_text(text)
    return True


def iter_raw_configs(results_root: Path) -> list[Path]:
    return sorted(
        path
        for path in results_root.rglob(RAW_CONFIG_NAME)
        if path.name == RAW_CONFIG_NAME and path.parent.name != "__pycache__"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    raw_configs = iter_raw_configs(args.results_root)
    changed = 0
    for raw_path in raw_configs:
        if export_one(raw_path, dry_run=args.dry_run):
            changed += 1

    action = "would_write" if args.dry_run else "wrote"
    print(f"raw_configs={len(raw_configs)}")
    print(f"{action}={changed}")


if __name__ == "__main__":
    main()
