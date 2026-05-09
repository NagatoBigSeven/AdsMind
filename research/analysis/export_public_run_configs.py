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
OPENROUTER_MODEL_ALIASES = {
    "google/gemini-2.5-pro": "gemini-2.5-pro",
    "x-ai/grok-4": "grok-4",
}
OCD62_RUN_MANIFEST_RE = re.compile(r"^ocd62_overlap12_run\d+_manifest_v1$")
OMIT_PUBLIC_KEYS = {
    "default_headers",
    "llm_default_headers",
    "notes",
    "recovery_note",
}
_OMIT = object()


def _normalize_public_string(value: str, path: tuple[str, ...], normalizations: list[str]) -> str:
    if value.startswith("benchmark_slabs/"):
        normalizations.append(".".join((*path, "cmu20_slab_path_normalized")))
        return value.replace("benchmark_slabs/", "datasets/cmu20/", 1)
    if OCD62_RUN_MANIFEST_RE.match(value):
        normalizations.append(".".join((*path, "ocd62_manifest_version_normalized")))
        return "ocd62_overlap12_manifest_v1"

    return value


def _canonical_transport_variant(value: str) -> str:
    lowered = value.lower()
    if "openrouter" in lowered or "grok4-compatible" in lowered:
        return "openrouter"
    if "anthropic" in lowered:
        return "anthropic-official"
    if "openai" in lowered:
        return "openai-official"
    return value


def _normalize_public_config(public: dict[str, Any]) -> list[str]:
    normalizations: list[str] = []

    def walk(value: Any, path: tuple[str, ...]) -> Any:
        if isinstance(value, dict):
            for key, child in list(value.items()):
                value[key] = walk(child, (*path, str(key)))

            llm_model = value.get("llm_model")
            if isinstance(llm_model, str) and llm_model in OPENROUTER_MODEL_ALIASES:
                value.setdefault("openrouter_model_id", llm_model)
                value["llm_model"] = OPENROUTER_MODEL_ALIASES[llm_model]
                normalizations.append(".".join((*path, "llm_model_openrouter_alias")))

            model = value.get("model")
            if isinstance(model, str) and model in OPENROUTER_MODEL_ALIASES:
                value.setdefault("openrouter_model_id", model)
                value["model"] = OPENROUTER_MODEL_ALIASES[model]
                normalizations.append(".".join((*path, "model_openrouter_alias")))

            transport_variant = value.get("transport_variant")
            if isinstance(transport_variant, str):
                canonical = _canonical_transport_variant(transport_variant)
                if canonical != transport_variant:
                    value["transport_variant"] = canonical
                    normalizations.append(".".join((*path, "transport_variant_normalized")))

            return value

        if isinstance(value, list):
            return [walk(child, (*path, "[]")) for child in value]

        if isinstance(value, str):
            return _normalize_public_string(value, path, normalizations)

        return value

    walk(public, ())

    frozen_config = public.get("frozen_config")
    if isinstance(frozen_config, dict):
        backend = frozen_config.get("llm_backend")
        base_url = frozen_config.get("llm_base_url")
        if backend == "openrouter" or base_url == "https://openrouter.ai/api/v1":
            public["_public_config"]["provider_transport"] = "openrouter"
            model = frozen_config.get("llm_model")
            if isinstance(model, str):
                public["_public_config"]["model_family"] = model

    return sorted(set(normalizations))


def _should_omit_public_field(key: str, child: Any) -> bool:
    lowered_key = key.lower()
    if lowered_key in OMIT_PUBLIC_KEYS:
        return True
    if (
        lowered_key == "manifest_version"
        and isinstance(child, str)
        and "recovery" in child.lower()
    ):
        return True
    return False


def _sanitize(
    value: Any,
    path: tuple[str, ...],
    redacted: list[str],
    omitted: list[str],
) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, child in value.items():
            child_path = (*path, str(key))
            if _should_omit_public_field(str(key), child):
                omitted.append(".".join(child_path))
                continue
            if SENSITIVE_KEY_RE.search(str(key)):
                sanitized[key] = "<redacted>"
                redacted.append(".".join(child_path))
            else:
                sanitized_child = _sanitize(child, child_path, redacted, omitted)
                if sanitized_child is not _OMIT:
                    sanitized[key] = sanitized_child
        return sanitized

    if isinstance(value, list):
        sanitized_items = []
        for child in value:
            sanitized_child = _sanitize(child, (*path, "[]"), redacted, omitted)
            if sanitized_child is not _OMIT:
                sanitized_items.append(sanitized_child)
        return sanitized_items

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
    omitted: list[str] = []
    public = _sanitize(raw, (), redacted, omitted)
    public["_public_config"] = {
        "schema_version": 1,
        "source_file": RAW_CONFIG_NAME,
        "redacted_fields": sorted(set(redacted)),
        "omitted_operational_field_count": len(set(omitted)),
    }
    public["_public_config"]["normalized_fields"] = _normalize_public_config(public)

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
