"""Markdown report generation for the AdsMind summarizer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from adsmind.tools.common import ensure_output_dir
from adsmind.tools.visualization import (
    render_best_structure_png,
    render_iteration_energy_curve,
)


def _safe_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def _md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _relative_link(target: Path, base_dir: Path) -> str:
    return os.path.relpath(target, start=base_dir).replace(os.sep, "/")


def _resolve_artifact_path(value: Any, output_dir: Path) -> Optional[Path]:
    if not value:
        return None
    candidate = Path(str(value))
    if candidate.exists():
        return candidate
    same_dir = output_dir / candidate.name
    if same_dir.exists():
        return same_dir
    return candidate


def _attempt_table(attempt_records: list[Dict[str, Any]]) -> str:
    if not attempt_records:
        return "No physical execution attempts were recorded.\n"

    lines = [
        "| Iteration | Status | Energy (eV) | Planned site | Actual site | Slip | Dissociated |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for idx, record in enumerate(attempt_records, start=1):
        energy = record.get("most_stable_energy_eV")
        try:
            energy_text = "" if energy is None else f"{float(energy):.3f}"
        except (TypeError, ValueError):
            energy_text = _md_escape(energy)
        lines.append(
            "| {idx} | {status} | {energy} | {planned} | {actual} | {slip} | {diss} |".format(
                idx=record.get("attempt_index", idx),
                status=_md_escape(record.get("status")),
                energy=energy_text,
                planned=_md_escape(record.get("planned_site_type")),
                actual=_md_escape(record.get("actual_site_type")),
                slip=_md_escape(record.get("is_chemical_slip")),
                diss=_md_escape(record.get("is_dissociated")),
            )
        )
    return "\n".join(lines) + "\n"


def write_summarizer_report(
    *,
    state: Dict[str, Any],
    final_text: str,
    target_data: Optional[Dict[str, Any]],
    plan_used: Optional[Dict[str, Any]],
    source_type: str,
) -> Dict[str, Optional[str]]:
    """Write the terminal Markdown report and deterministic visual artifacts.

    Visualization failures are intentionally recorded in the report rather than
    raised, so reporting never changes the scientific search outcome.
    """
    output_dir = ensure_output_dir(state["session_id"])
    report_path = output_dir / "summary_report.md"
    best_png = output_dir / "best_configuration.png"
    curve_png = output_dir / "iteration_energy_curve.png"

    artifacts: Dict[str, Optional[str]] = {
        "summary_report_file": str(report_path),
        "best_configuration_png": None,
        "iteration_energy_curve_png": None,
        "visualization_error": None,
    }
    visualization_notes: list[str] = []

    target_data = target_data or {}
    best_structure = _resolve_artifact_path(target_data.get("best_structure_file"), output_dir)
    if source_type == "success" and best_structure is not None:
        try:
            render_best_structure_png(best_structure, best_png)
            artifacts["best_configuration_png"] = str(best_png)
        except Exception as exc:
            message = f"Best-configuration rendering unavailable: {exc}"
            artifacts["visualization_error"] = message
            visualization_notes.append(message)

    attempt_records = list(state.get("attempt_records", []) or [])
    try:
        render_iteration_energy_curve(attempt_records, curve_png)
        artifacts["iteration_energy_curve_png"] = str(curve_png)
    except Exception as exc:
        message = f"Iteration energy curve unavailable: {exc}"
        artifacts["visualization_error"] = (
            f"{artifacts['visualization_error']}; {message}"
            if artifacts["visualization_error"]
            else message
        )
        visualization_notes.append(message)

    best_energy = target_data.get("most_stable_energy_eV")
    try:
        best_energy_text = "N/A" if best_energy is None else f"{float(best_energy):.3f} eV"
    except (TypeError, ValueError):
        best_energy_text = _md_escape(best_energy)
    best_xyz_link = (
        _relative_link(best_structure, output_dir)
        if best_structure is not None
        else "N/A"
    )

    sections = [
        "# AdsMind Summarizer Report",
        "",
        "## Run Context",
        f"- Session ID: `{state.get('session_id', '')}`",
        f"- User request: {_md_escape(state.get('user_request', ''))}",
        f"- SMILES: `{state.get('smiles', '')}`",
        f"- Slab path: `{state.get('slab_path', '')}`",
        f"- Source type: `{source_type}`",
        "",
        "## Best Configuration",
        f"- Best adsorption energy: {best_energy_text}",
        f"- Best structure file: `{best_xyz_link}`",
    ]

    if artifacts["best_configuration_png"]:
        sections.extend(
            [
                "",
                f"![Best configuration]({_relative_link(best_png, output_dir)})",
            ]
        )
    if artifacts["iteration_energy_curve_png"]:
        sections.extend(
            [
                "",
                "## Iteration Energy Curve",
                f"![Iteration energy curve]({_relative_link(curve_png, output_dir)})",
            ]
        )
    if visualization_notes:
        sections.extend(["", "## Visualization Notes"])
        sections.extend(f"- {note}" for note in visualization_notes)

    sections.extend(
        [
            "",
            "## Iteration Summary",
            _attempt_table(attempt_records),
            "## Selected Plan",
            "```json",
            _safe_json(plan_used or {}),
            "```",
            "",
            "## Structured Analysis",
            "```json",
            _safe_json(target_data),
            "```",
            "",
            "## Summarizer Narrative",
            final_text.strip() or "No final narrative was returned.",
            "",
        ]
    )

    report_path.write_text("\n".join(sections), encoding="utf-8")
    return artifacts
