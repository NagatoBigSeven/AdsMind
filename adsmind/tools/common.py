"""Common helpers shared across the tools package."""

from pathlib import Path

OUTPUT_ROOT = Path("outputs")


def ensure_output_dir(session_id: str | None = None) -> Path:
    """Create and return the shared output directory or a session subdirectory."""
    OUTPUT_ROOT.mkdir(exist_ok=True)
    if session_id is None:
        return OUTPUT_ROOT

    session_dir = OUTPUT_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def sanitize_smiles_for_filename(smiles: str, strip_brackets: bool = False) -> str:
    """Convert a SMILES string into a filesystem-safe label."""
    sanitized = smiles.replace("=", "_").replace("#", "_")
    if strip_brackets:
        sanitized = sanitized.replace("[", "").replace("]", "")
    return sanitized
