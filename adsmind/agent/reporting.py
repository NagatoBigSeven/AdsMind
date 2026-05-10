"""Markdown report generation for the AdsMind summarizer.

The report is structured as a per-round reasoning log so a human scientist
can read what the agent thought, planned, and executed at each iteration —
not just the final winning configuration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

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


def _format_energy(value: Any, suffix: str = " eV") -> str:
    try:
        return f"{float(value):.3f}{suffix}"
    except (TypeError, ValueError):
        return _md_escape(value) if value is not None else "N/A"


def _quote_block(text: str) -> str:
    """Render multi-line text as a Markdown blockquote."""
    text = (text or "").strip()
    if not text:
        return "> _(no reasoning recorded)_"
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def _round_status_badge(record: Dict[str, Any]) -> str:
    status = record.get("status")
    if status != "success":
        return "❌ failed"
    if record.get("is_dissociated"):
        return "💥 dissociated"
    if (record.get("bond_change_count") or 0) > 0:
        return "⚠️ rearranged"
    return "✅ adsorbed"


def _round_title(record: Dict[str, Any]) -> str:
    plan = record.get("plan") or {}
    solution = plan.get("solution", {}) if isinstance(plan, dict) else {}
    site_type = solution.get("site_type") or "—"
    surf = solution.get("surface_binding_atoms") or []
    surf_str = "/".join(str(s) for s in surf) if surf else "—"
    energy = record.get("most_stable_energy_eV")
    energy_str = _format_energy(energy)
    badge = _round_status_badge(record)
    return f"Round {record.get('attempt_index', '?')} — `{site_type}` @ {surf_str}  ·  {badge}  ·  E = {energy_str}"


def _plan_bullets(plan: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(plan, dict):
        return ["- _(plan unavailable)_"]
    solution = plan.get("solution", {}) or {}
    bullets = [
        f"- **adsorbate_type**: `{plan.get('adsorbate_type', '—')}`",
        f"- **site_type**: `{solution.get('site_type', '—')}`",
        f"- **surface_binding_atoms**: `{solution.get('surface_binding_atoms', [])}`",
        f"- **adsorbate_binding_indices**: `{solution.get('adsorbate_binding_indices', [])}`",
    ]
    extras = []
    for key in ("touch_sphere_size", "overlap_thr", "conformers_per_site_cap", "relax_top_n", "action"):
        if key in solution:
            extras.append(f"- **{key}**: `{solution.get(key)}`")
    bullets.extend(extras)
    return bullets


def _execution_bullets(tool_logs: Optional[Iterable[str]]) -> List[str]:
    if not tool_logs:
        return ["- _(no execution log captured)_"]
    return [f"- {line}" for line in tool_logs]


def _result_bullets(record: Dict[str, Any], output_dir: Path) -> List[str]:
    status = record.get("status")
    if status != "success":
        return [
            f"- **status**: `{status}`",
            f"- **message**: {_md_escape(record.get('message'))}",
        ]
    bullets = [
        f"- **planned site**: `{record.get('planned_site_type', '—')}`  →  **actual**: `{record.get('actual_site_type', '—')}`",
        f"- **chemical slip**: {'yes' if record.get('is_chemical_slip') else 'no'}",
        f"- **bond change count**: `{record.get('bond_change_count')}`",
        f"- **dissociated**: {'yes' if record.get('is_dissociated') else 'no'}",
        f"- **most stable energy**: `{_format_energy(record.get('most_stable_energy_eV'))}`",
    ]
    best_xyz = record.get("best_structure_file")
    if best_xyz:
        resolved = _resolve_artifact_path(best_xyz, output_dir)
        if resolved is not None:
            bullets.append(
                f"- **structure file**: [`{Path(str(best_xyz)).name}`]({_relative_link(resolved, output_dir)})"
            )
        else:
            bullets.append(f"- **structure file**: `{Path(str(best_xyz)).name}`")
    return bullets


def _validation_failure_block(failure: Dict[str, Any]) -> List[str]:
    idx = failure.get("validation_index")
    lines = [
        f"#### ⚠️ Validation retry {idx} — plan rejected",
        f"- **Reason**: {_md_escape(failure.get('error'))}",
    ]
    reasoning = failure.get("failed_plan_reasoning")
    if reasoning:
        lines.extend(["", "Planner reasoning that was rejected:", _quote_block(reasoning)])
    failed_plan = failure.get("failed_plan")
    if failed_plan:
        lines.extend(
            [
                "",
                "<details><summary>Rejected plan JSON</summary>",
                "",
                "```json",
                _safe_json(failed_plan),
                "```",
                "",
                "</details>",
            ]
        )
    raw_output = failure.get("failed_raw_output")
    if raw_output:
        lines.extend(
            [
                "",
                "<details><summary>Raw LLM output (failed to parse as JSON)</summary>",
                "",
                "```text",
                str(raw_output),
                "```",
                "",
                "</details>",
            ]
        )
    return lines


def _termination_section(record: Dict[str, Any]) -> List[str]:
    rnd = record.get("round", "?")
    plan = record.get("plan") or {}
    sections = [
        f"### Round {rnd} — 🛑 Agent decided to terminate",
        "",
        "**🧠 Planner reasoning**",
        "",
        _quote_block(record.get("reasoning") or ""),
    ]
    if isinstance(plan, dict) and plan:
        sections.extend(
            [
                "",
                "<details><summary>Termination plan JSON</summary>",
                "",
                "```json",
                _safe_json(plan),
                "```",
                "",
                "</details>",
            ]
        )
    return sections


def _resolve_llm_model(state: Dict[str, Any]) -> Optional[str]:
    """Best-effort resolution of the effective LLM model name."""
    overrides = state.get("llm_config") or {}
    if isinstance(overrides, dict) and overrides.get("model"):
        return str(overrides["model"])
    backend_name = state.get("llm_backend")
    if not backend_name:
        return None
    try:
        from adsmind.llms import get_llm_backend  # local import keeps reporting cheap

        backend = get_llm_backend(backend_name)
        config = backend.get_default_config(api_key=state.get("api_key", ""))
        return getattr(config, "model", None)
    except Exception:
        return None


def _resolve_calculator_model(state: Dict[str, Any]) -> Optional[str]:
    """Best-effort resolution of the effective calculator model name."""
    overrides = state.get("calculator_config") or {}
    if isinstance(overrides, dict) and overrides.get("model"):
        return str(overrides["model"])
    backend_name = state.get("calculator_backend")
    if not backend_name:
        return None
    try:
        from adsmind.calculators import get_backend  # local import

        backend = get_backend(backend_name)
        # Some backends (e.g., MACE) require has_gpu; others ignore it.
        try:
            import torch

            has_gpu = bool(torch.cuda.is_available())
        except Exception:
            has_gpu = False
        try:
            config = backend.get_default_config(has_gpu=has_gpu)
        except TypeError:
            config = backend.get_default_config()
        return getattr(config, "model", None)
    except Exception:
        return None


def _setup_lines(state: Dict[str, Any], source_type: str) -> List[str]:
    llm_backend = state.get("llm_backend") or "—"
    llm_model = _resolve_llm_model(state)
    llm_label = f"`{llm_backend}`" + (f" (model: `{llm_model}`)" if llm_model else "")

    calc_backend = state.get("calculator_backend") or "—"
    calc_model = _resolve_calculator_model(state)
    calc_label = f"`{calc_backend}`" + (f" (model: `{calc_model}`)" if calc_model else "")

    seed = state.get("random_seed")
    seed_label = f"`{seed}`" if seed is not None else "_(unset)_"

    return [
        f"- **SMILES**: `{state.get('smiles', '')}`",
        f"- **Slab**: `{state.get('slab_path', '')}`",
        f"- **User request**: {_md_escape(state.get('user_request', ''))}",
        f"- **Session ID**: `{state.get('session_id', '')}`",
        f"- **LLM backend**: {llm_label}",
        f"- **Calculator backend**: {calc_label}",
        f"- **Random seed**: {seed_label}",
        f"- **Relaxation mode**: `{state.get('relaxation_mode', '—')}`",
        f"- **Max attempts**: `{state.get('max_attempts', '—')}`",
        f"- **Source type**: `{source_type}`",
    ]


def _round_section(
    record: Dict[str, Any],
    validation_failures: List[Dict[str, Any]],
    output_dir: Path,
) -> List[str]:
    plan = record.get("plan") or {}
    analysis_json = {
        k: record.get(k)
        for k in (
            "status",
            "most_stable_energy_eV",
            "bond_change_count",
            "is_dissociated",
            "is_chemical_slip",
            "planned_site_type",
            "actual_site_type",
            "best_structure_file",
            "generated_conformers_file",
            "relaxation_trajectory_file",
            "message",
        )
    }

    sections: List[str] = [f"### {_round_title(record)}"]

    for failure in validation_failures:
        sections.append("")
        sections.extend(_validation_failure_block(failure))

    sections.extend(
        [
            "",
            "**🧠 Planner reasoning**",
            "",
            _quote_block(record.get("planner_reasoning") or ""),
            "",
            "**📋 Plan**",
            "",
            *_plan_bullets(plan),
            "",
            "**⚙️ Execution**",
            "",
            *_execution_bullets(record.get("tool_logs")),
            "",
            "**📊 Result**",
            "",
            *_result_bullets(record, output_dir),
        ]
    )
    history_entry = record.get("history_entry")
    if history_entry:
        sections.extend(
            [
                "",
                "**📝 Round verdict**",
                "",
                f"> {history_entry}",
            ]
        )

    sections.extend(
        [
            "",
            "<details><summary>Raw plan & analysis JSON</summary>",
            "",
            "```json",
            _safe_json({"plan": plan, "analysis": analysis_json}),
            "```",
            "",
            "</details>",
        ]
    )
    return sections


def _attempt_table(attempt_records: List[Dict[str, Any]]) -> str:
    if not attempt_records:
        return "_No physical execution attempts were recorded._\n"

    lines = [
        "| # | Status | Energy (eV) | Planned site | Actual site | Slip | Dissociated |",
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
                slip="yes" if record.get("is_chemical_slip") else "no",
                diss="yes" if record.get("is_dissociated") else "no",
            )
        )
    return "\n".join(lines) + "\n"


def _tldr_lines(
    state: Dict[str, Any],
    target_data: Optional[Dict[str, Any]],
    plan_used: Optional[Dict[str, Any]],
    source_type: str,
    attempt_records: List[Dict[str, Any]],
) -> List[str]:
    target_data = target_data or {}
    n_rounds = len(attempt_records)
    n_validation_retries = len(state.get("validation_attempt_records", []) or [])
    plan_solution = (plan_used or {}).get("solution", {}) if plan_used else {}

    lines: List[str] = []
    if source_type == "success":
        lines.append(
            f"- **Best E_ads**: `{_format_energy(target_data.get('most_stable_energy_eV'))}`  "
            f"at `{plan_solution.get('site_type', '—')}` @ "
            f"`{plan_solution.get('surface_binding_atoms', [])}`"
        )
        site_info = target_data.get("site_analysis", {}) or {}
        if site_info.get("is_chemical_slip"):
            lines.append(
                f"- **Chemical slip detected**: planned `{site_info.get('planned_site_type')}` "
                f"→ actual `{site_info.get('actual_site_type')}`"
            )
    else:
        lines.append("- **Outcome**: ❌ no stable adsorption configuration found")

    best_diss = state.get("best_dissociated_result") or {}
    if source_type == "success" and best_diss:
        e_mol = target_data.get("most_stable_energy_eV")
        e_diss = best_diss.get("most_stable_energy_eV")
        try:
            if float(e_diss) < float(e_mol):
                lines.append(
                    f"- ⚠️ **Dissociated state more stable**: "
                    f"`{_format_energy(e_diss)}` vs molecular `{_format_energy(e_mol)}` "
                    f"(metastable molecular adsorption)"
                )
        except (TypeError, ValueError):
            pass

    lines.append(f"- **Rounds executed**: {n_rounds}  ·  **validator retries**: {n_validation_retries}")
    if state.get("termination_record"):
        lines.append("- **Agent terminated early**: planner declared convergence (see final round)")
    return lines


def write_summarizer_report(
    *,
    state: Dict[str, Any],
    final_text: str,
    target_data: Optional[Dict[str, Any]],
    plan_used: Optional[Dict[str, Any]],
    source_type: str,
) -> Dict[str, Optional[str]]:
    """Write the per-round reasoning Markdown report and visual artifacts.

    Visualization failures are recorded in the report rather than raised, so
    reporting never changes the scientific search outcome.
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
    visualization_notes: List[str] = []

    target_data = target_data or {}
    attempt_records: List[Dict[str, Any]] = list(state.get("attempt_records", []) or [])
    validation_records: List[Dict[str, Any]] = list(
        state.get("validation_attempt_records", []) or []
    )

    best_structure = _resolve_artifact_path(target_data.get("best_structure_file"), output_dir)
    if source_type == "success" and best_structure is not None:
        try:
            render_best_structure_png(best_structure, best_png)
            artifacts["best_configuration_png"] = str(best_png)
        except Exception as exc:
            message = f"Best-configuration rendering unavailable: {exc}"
            artifacts["visualization_error"] = message
            visualization_notes.append(message)

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

    slab_label = Path(str(state.get("slab_path", "") or "?")).name or "—"
    sections: List[str] = [
        f"# AdsMind Reasoning Log — `{state.get('smiles', '')}` on `{slab_label}`",
        "",
        "## TL;DR",
        "",
        *_tldr_lines(state, target_data, plan_used, source_type, attempt_records),
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
                f"![Iteration energy curve]({_relative_link(curve_png, output_dir)})",
            ]
        )
    if visualization_notes:
        sections.append("")
        sections.extend(f"> _Visualization note: {note}_" for note in visualization_notes)

    sections.extend(
        [
            "",
            "## Setup",
            "",
            *_setup_lines(state, source_type),
            "",
            "## Round-by-Round Reasoning Log",
            "",
        ]
    )

    termination_record = state.get("termination_record")

    if not attempt_records and not validation_records and not termination_record:
        sections.append("_No rounds were executed._")
    else:
        # Group validation failures by the round they preceded.
        failures_by_round: Dict[int, List[Dict[str, Any]]] = {}
        for failure in validation_records:
            rnd = failure.get("for_round") or 1
            failures_by_round.setdefault(rnd, []).append(failure)

        for record in attempt_records:
            rnd = record.get("attempt_index")
            sections.extend(
                _round_section(
                    record,
                    failures_by_round.pop(rnd, []),
                    output_dir,
                )
            )
            sections.append("")

        # Any leftover validation failures (e.g., terminal failure that never
        # produced a tool execution) get rendered as their own pseudo-round.
        for rnd in sorted(failures_by_round.keys()):
            sections.append(f"### Round {rnd} — ❌ never executed (validation cap reached)")
            for failure in failures_by_round[rnd]:
                sections.append("")
                sections.extend(_validation_failure_block(failure))
            sections.append("")

        # When the planner explicitly chose to terminate, surface its reasoning
        # so readers can see why the agent decided to stop.
        if termination_record:
            sections.extend(_termination_section(termination_record))
            sections.append("")

    sections.extend(
        [
            "## Final Discussion",
            "",
            (final_text or "").strip() or "_No final narrative was returned._",
            "",
            "## Iteration Summary Table",
            "",
            _attempt_table(attempt_records),
        ]
    )

    report_path.write_text("\n".join(sections), encoding="utf-8")
    return artifacts


def build_terminal_tldr(
    state: Dict[str, Any],
    target_data: Optional[Dict[str, Any]],
    plan_used: Optional[Dict[str, Any]],
    source_type: str,
) -> str:
    """Compact terminal-friendly summary for end-of-run printout."""
    attempt_records = list(state.get("attempt_records", []) or [])
    lines = ["TL;DR"]
    for raw in _tldr_lines(state, target_data, plan_used, source_type, attempt_records):
        # Strip Markdown bullet formatting for terminal readability.
        clean = raw.lstrip("- ").replace("**", "").replace("`", "")
        lines.append(f"  • {clean}")
    if attempt_records:
        lines.append("Per-round verdicts:")
        for rec in attempt_records:
            verdict = rec.get("history_entry") or rec.get("message") or "(no verdict)"
            lines.append(f"  [{rec.get('attempt_index')}] {verdict}")
    return "\n".join(lines)
