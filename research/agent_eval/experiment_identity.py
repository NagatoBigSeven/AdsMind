"""Stable experiment identities for research result paths.

Paper-facing result directories encode the LLM family/version and MACE-MP-0
force-field size. API transport details are retained only where needed to rerun
experiments; they are not benchmark identity dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackendIdentity:
    key: str
    result_dir: str
    display_name: str
    llm_model: str
    force_field: str
    calculator_backend: str = "mace"
    force_field_model: str = "mace_mp0"
    force_field_size: str = "small"


BASIC_BACKEND_IDENTITIES: dict[str, BackendIdentity] = {
    "gpt": BackendIdentity(
        key="gpt",
        result_dir="gpt54_mace_mp0_small",
        display_name="GPT-5.4",
        llm_model="gpt-5.4-2026-03-05",
        force_field="MACE-MP-0 small",
    ),
    "claude": BackendIdentity(
        key="claude",
        result_dir="claude_sonnet46_mace_mp0_small",
        display_name="Claude Sonnet 4.6",
        llm_model="claude-sonnet-4-6",
        force_field="MACE-MP-0 small",
    ),
    "gemini": BackendIdentity(
        key="gemini",
        result_dir="gemini25pro_mace_mp0_small",
        display_name="Gemini 2.5 Pro",
        llm_model="gemini-2.5-pro",
        force_field="MACE-MP-0 small",
    ),
    "grok": BackendIdentity(
        key="grok",
        result_dir="grok4_mace_mp0_small",
        display_name="Grok-4",
        llm_model="grok-4",
        force_field="MACE-MP-0 small",
    ),
}

RUN3_BACKEND_IDENTITIES: dict[str, BackendIdentity] = {
    **BASIC_BACKEND_IDENTITIES,
    "gemini": BackendIdentity(
        key="gemini",
        result_dir="gemini25pro_mace_mp0_small",
        display_name="Gemini 2.5 Pro",
        llm_model="gemini-2.5-pro",
        force_field="MACE-MP-0 small",
    ),
    "grok": BackendIdentity(
        key="grok",
        result_dir="grok4_mace_mp0_small",
        display_name="Grok-4",
        llm_model="grok-4",
        force_field="MACE-MP-0 small",
    ),
}

MACE_LARGE_GPT54 = BackendIdentity(
    key="gpt",
    result_dir="gpt54_mace_mp0_large",
    display_name="GPT-5.4",
    llm_model="gpt-5.4-2026-03-05",
    force_field="MACE-MP-0 large",
    force_field_size="large",
)

BACKEND_KEYS = tuple(BASIC_BACKEND_IDENTITIES)


def backend_identity(key: str, *, run_name: str | None = None) -> BackendIdentity:
    """Return the protocol identity for a backend key."""
    identities = RUN3_BACKEND_IDENTITIES if run_name == "run3" else BASIC_BACKEND_IDENTITIES
    return identities[key]


def backend_result_dir(key: str, *, run_name: str | None = None) -> str:
    """Return the directory name for a backend key."""
    return backend_identity(key, run_name=run_name).result_dir


def identity_from_result_dir(result_dir: str) -> BackendIdentity | None:
    """Return the identity encoded by a result directory name."""
    for identity in (*BASIC_BACKEND_IDENTITIES.values(), *RUN3_BACKEND_IDENTITIES.values(), MACE_LARGE_GPT54):
        if identity.result_dir == result_dir:
            return identity
    return None


def identity_from_path(path: str | Path) -> BackendIdentity | None:
    """Infer the experiment identity encoded in a result path."""
    parts = Path(path).parts
    for part in reversed(parts):
        identity = identity_from_result_dir(part)
        if identity is not None:
            return identity
    for part in reversed(parts):
        for identity in (*BASIC_BACKEND_IDENTITIES.values(), *RUN3_BACKEND_IDENTITIES.values(), MACE_LARGE_GPT54):
            if identity.result_dir in part:
                return identity
    return None


def identity_from_label(label: str) -> BackendIdentity | None:
    """Infer a backend identity from a legacy human label or backend key."""
    raw = label.strip()
    identity = identity_from_result_dir(raw)
    if identity is not None:
        return identity

    normalized = raw.lower()
    if normalized in BASIC_BACKEND_IDENTITIES:
        return BASIC_BACKEND_IDENTITIES[normalized]
    aliases = {
        "gpt_5.4": "gpt",
        "gpt-5.4": "gpt",
        "gpt54": "gpt",
        "gpt54_mace_mp0_small": "gpt",
        "gemini_2.5_pro": "gemini",
        "gemini-2.5-pro": "gemini",
        "gemini25pro_mace_mp0_small": "gemini",
        "grok_4": "grok",
        "grok-4": "grok",
        "grok4": "grok",
        "grok4_mace_mp0_small": "grok",
        "claude_sonnet_4.6": "claude",
        "claude-sonnet-4.6": "claude",
        "claude_sonnet46_mace_mp0_small": "claude",
    }
    key = aliases.get(normalized)
    return BASIC_BACKEND_IDENTITIES[key] if key else None


def summary_metadata(identity: BackendIdentity) -> dict[str, str]:
    """Return stable CSV metadata columns for one experiment identity."""
    return {
        "backend_key": identity.key,
        "backend": identity.result_dir,
        "llm_model": identity.llm_model,
        "force_field": identity.force_field,
        "calculator_backend": identity.calculator_backend,
        "force_field_model": identity.force_field_model,
        "force_field_size": identity.force_field_size,
    }
