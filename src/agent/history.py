"""History formatting helpers for agent post-analysis state updates."""

from typing import Optional

ENERGY_SIMILARITY_TOL_EV = 0.05


def format_plan_description(plan_json: Optional[dict]) -> str:
    """Format the planner solution into a compact history string."""
    solution = (plan_json or {}).get("solution", {})
    return (
        f"{solution.get('site_type')} @ {solution.get('surface_binding_atoms')} "
        f"(Index {solution.get('adsorbate_binding_indices')})"
    )


def build_history_entry(
    current_plan: Optional[dict],
    analysis_data: dict,
    best_result: Optional[dict],
) -> str:
    """Generate a history entry without mutating the graph state."""
    plan_desc = format_plan_description(current_plan)
    status = analysis_data.get("status")

    if status == "fatal_error":
        return f"【FATAL ERROR】 Plan: {plan_desc} -> {analysis_data.get('message')}"

    energy = analysis_data.get("most_stable_energy_eV", "N/A")
    bond_change = analysis_data.get("bond_change_count", 0)
    is_dissociated = analysis_data.get("is_dissociated", False)

    site_info = analysis_data.get("site_analysis", {})
    actual_site = site_info.get("actual_site_type", "unknown")
    planned_site = site_info.get("planned_site_type", "unknown")
    is_chem_slip = site_info.get("is_chemical_slip", False)
    planned_syms = site_info.get("planned_symbols", [])
    actual_syms = site_info.get("actual_symbols", [])

    site_msg = f"Site: {actual_site} ({','.join(actual_syms)})"
    if is_chem_slip:
        planned_str = "-".join(planned_syms)
        actual_str = "-".join(actual_syms)
        site_msg = (
            f"⚠️【Unstable Site Warning】⚠️: "
            f"Planned {planned_site} ({planned_str}) is unstable, adsorbate spontaneously slipped to "
            f"{actual_site} ({actual_str})."
            f"This means {planned_str} has insufficient affinity for this adsorbate. "
            f"Please **FORBID** testing {planned_str} type sites again!"
        )
    elif actual_site != "unknown" and planned_site != "unknown" and actual_site != planned_site:
        site_msg = f"⚠️ Geometric Slip: {planned_site} -> {actual_site}"

    tag = ""
    if best_result and isinstance(energy, (int, float)):
        best_e = best_result.get("most_stable_energy_eV", float("inf"))
        current_fp = site_info.get("site_fingerprint", "")
        best_fp = best_result.get("analysis_json", {}).get("site_analysis", {}).get("site_fingerprint", "")

        if current_plan == best_result.get("plan"):
            tag = " [🌟 New Best]"
        elif abs(energy - best_e) < ENERGY_SIMILARITY_TOL_EV:
            if current_fp and best_fp and current_fp == best_fp:
                tag = " [🔄 Converged to known best]"
            else:
                tag = " [⚠️ Energy Degenerate but Geometrically Distinct]"

    site_msg = f"{site_msg}{tag}"

    if status == "success":
        if is_dissociated:
            result_str = "❌ Dissociated"
        elif bond_change > 0:
            result_str = f"⚠️ Rearrangement(BC={bond_change})"
        else:
            result_str = "✅ Perfect Adsorption"

        if isinstance(energy, (int, float)):
            return f"【{result_str}】 {plan_desc} -> {site_msg} | E={energy:.3f} eV"
        return f"【{result_str}】 {plan_desc} -> {site_msg} | E={energy}"

    return f"【Calculation Failed】 {plan_desc} -> Reason: {analysis_data.get('message')}"
