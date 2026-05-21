"""Prompt construction helpers for the AdsMind planner."""

from textwrap import dedent


def _planner_reasoning_step_1(
    history: str,
    enable_slip_feedback: bool,
    enable_forbid: bool,
    enable_termination: bool,
) -> str:
    lines = [
        f"1. **Analyze Old Plans:** Check {history}. Which sites and orientations have you tested? Which succeeded? What were the adsorption energies? Which failed?",
        "   - **Note:** If a plan detected a reactivity change (e.g., adsorbate dissociation or rearrangement) or bond change count > 0, it is considered a failure.",
    ]
    if enable_slip_feedback:
        lines.extend(
            [
                '   - **Special Note [Unstable Site Warning]:** If the history shows "Chemical Slip" occurred, this proves the initially planned site is thermodynamically unstable.',
                '   - **Learning Conclusion:** Consider the initial site type that slipped as "invalid/unstable".',
            ]
        )
    if enable_termination:
        lines.extend(
            [
                "   - **Critical Termination Signal:** You must strictly observe the Tags in the history:",
                '     - **[🔄 Converged to known best]**: This means the new plan converged to the EXACT SAME geometry and energy as a previous best result. **You must immediately output `"action": "terminate"`**.',
                '     - **[⚠️ Energy Degenerate but Geometrically Distinct]**: This means you found a DIFFERENT site that happens to have the same energy. This is a VALID new discovery. **Do NOT terminate**.',
                '   - **Precision Note:** Float32 is used. Energy differences < 0.05 eV are considered similar due to numerical noise, but you must rely on the history tags above when deciding whether a state is duplicate or degenerate.',
                '   - **Do not invent new plans just to "try something different".** If major high-symmetry sites have all been tested and results are close in energy (or all slipped to the same place), directly output `terminate`.',
            ]
        )
    else:
        lines.append(
            "   - **Termination disabled for this run:** Keep proposing new physically sensible plans until you hit the hard attempt limit."
        )
    lines.extend(
        [
            '   - **Surface Heterogeneity Analysis:** If the same site type gave significantly different energies, inspect the `site_fingerprint` and assume chemically distinct environments may exist on alloy surfaces.',
            "   - **Decision:** If you suspect a better site exists due to heterogeneity, try fine-tuning `surface_binding_atoms` or mention the need to further explore that environment in `reasoning`.",
        ]
    )
    return "\n".join(lines)


def _planner_reasoning_step_2(
    history: str,
    available_sites_description: str,
    enable_forbid: bool,
    enable_termination: bool,
) -> str:
    lines = [
        "2. **Formulate New Plan:** Your goal is to find the configuration with the lowest adsorption energy.",
        '   - **Physical Consistency Principle:** If the tool reports "actual_site_type: desorbed" but the energy is very low (e.g., < -1.0 eV), this is a software label error. Judge based on the energy value: this is actually a stable chemisorbed state.',
    ]
    if enable_forbid:
        lines.append(
            "   - **Avoid Pitfalls:** Do not plan again for site types identified as unstable in Step 1 unless you have a very strong geometric reason to believe a new environment can stabilize them."
        )
    lines.extend(
        [
            f'   - **Strict Site Naming Restrictions:** `site_type` can only be one of "ontop", "bridge", or "hollow". Even if {available_sites_description} contains richer labels, your JSON must still use only these three canonical names.',
            f'   - If {history} is "None", propose the best initial plan.',
            f'   - If {history} already contains plans, you must propose a completely new plan different from all plans in {history}.',
        ]
    )
    if enable_termination:
        lines.append(
            "   - **Convergence Principle:** If different initial sites eventually converge to the same configuration, do not invent unreasonable plans just to be different. Output the terminate instruction."
        )
    lines.append(
        "   - **Note:** The process has a hard attempt cap. Use the remaining attempts systematically."
    )
    return "\n".join(lines)


def _predicted_energy_instruction(enable_executor: bool) -> str:
    if enable_executor:
        return ""
    return dedent(
        """
        **--- Executor Disabled (LLM-as-Oracle Mode) ---**
        The downstream MACE-MP-0 small relaxation will NOT be run for this plan.
        You must therefore additionally predict the adsorption energy that the
        MACE-MP-0 small force field would produce if it were to relax this
        configuration. Predict the MACE-MP-0 small relaxed energy (in eV), not a
        DFT value. The history you see was generated by the same prediction
        mechanism in previous iterations.

        Add the following field to your JSON output:
          "predicted_relaxed_energy_eV": <signed float, in eV, your best estimate>
        Output the number only; do not append units or comments. If you cannot
        make a confident prediction, still emit a numerical best guess (do not
        use null).
        **--- End Executor Disabled ---**
        """
    ).strip()


def build_planner_prompt(
    *,
    smiles: str,
    slab_path: str,
    surface_composition: str,
    available_sites_description: str,
    user_request: str,
    history: str,
    max_attempts: int,
    autoadsorbate_context: str,
    enable_slip_feedback: bool = True,
    enable_forbid: bool = True,
    enable_termination: bool = True,
    enable_executor: bool = True,
) -> str:
    """Build the planner prompt with ablation-sensitive sections."""
    return dedent(
        f"""
        You are a computational chemistry expert specializing in heterogeneous catalysis and surface science.
        Your task is to systematically find the **lowest energy** adsorption configuration for a given adsorbate-catalyst system by iteratively testing different adsorption sites and orientations.

        **Input Information:**
        - SMILES: {smiles}
        - Slab File Path: {slab_path} (supports XYZ, CIF, PDB, SDF, MOL, POSCAR formats)
        - Surface Composition: {surface_composition}
        - Available Sites List: {available_sites_description}
        - User Request: {user_request}

        **--- History (All previous successful and failed attempts) ---**
        {history}
        **--- End of History ---**

        {_predicted_energy_instruction(enable_executor)}

        ### 🧠 Your Reasoning Steps (Must be strictly followed):
        0. **SMILES Consistency Check (Crucial):**
           - Check the atom list provided by `autoadsorbate_context`.
           - **Check Hybridization:** If the user requests a saturated alkyl but the SMILES shows `SP2` or `SP`, explicitly warn in `reasoning` that the SMILES and user description do not match. Continue based on the SMILES.
           - **Check Radicals:** Confirm whether the selected binding atom(s) actually have unpaired electrons (`radical_electrons > 0`) if you plan `ReactiveSpecies`.
        {_planner_reasoning_step_1(history, enable_slip_feedback, enable_forbid, enable_termination)}
        {_planner_reasoning_step_2(history, available_sites_description, enable_forbid, enable_termination)}
        3. **Analyze Request:** What is the user's core intent? (e.g., specific atom adsorbed with specific orientation at specific site)
        4. **Analyze Adsorbate (SMILES: {smiles}):**
           - Major functional groups;
           - RDKit library has analyzed this SMILES and returned the following factual heavy atom index list:
           {autoadsorbate_context}
           - **Your Task:** Strictly refer to the index list above and select the correct `adsorbate_binding_indices` in Step 6.
           - **Warning:** Strictly forbid guessing indices. If indices do not match, your plan will fail.
        5. **Analyze Surface:** Refer to {available_sites_description} and only plan for existing site combinations.
        6. **Formulate Plan:**
           - `site_type`: Select site (ontop / bridge / hollow)
           - `surface_binding_atoms`: Surface atoms involved in bonding
           - `adsorbate_binding_indices`: Indices of adsorbate atoms involved in bonding
           - `relax_top_n`: default 1
           - `touch_sphere_size`: default 2
           - `overlap_thr`: default 0.1
           - `conformers_per_site_cap`: default 4
        7. **Output JSON Object.**

        ---

        ### Output Format (Strict JSON, no Markdown syntax):
        {{
          "reasoning": "Your detailed reasoning process...",
          "adsorbate_type": "Molecule" or "ReactiveSpecies",
          "solution": {{
            "action": "continue" or "terminate",
            "site_type": "...",
            "surface_binding_atoms": [...],
            "adsorbate_binding_indices": [...],
            "relax_top_n": 1,
            "touch_sphere_size": 2,
            "overlap_thr": 0.1,
            "conformers_per_site_cap": 4
          }}
        }}

        ---

        ### ⚠️ Critical Constraints (Must be strictly followed):

        **1. Chemical Type Rules**
        - **`adsorbate_type`: "Molecule"**:
          - Used for adsorbing complete, stable molecules (e.g., `CO`).
          - `adsorbate_binding_indices` must point to atoms with lone pairs or chemically valid donor atoms.
          - Do not plan "Molecule" adsorption via saturated atoms.
        - **`adsorbate_type`: "ReactiveSpecies"**:
          - Used for adsorbing fragments/radicals (e.g., `[CH3]`, `[CH2]O`).
          - `adsorbate_binding_indices` must point to atoms with unpaired electrons.
          - Do not plan "ReactiveSpecies" adsorption via saturated atoms.

        **2. Site Alignment Rules**
        - `site_type: "ontop"` must correspond to `len(adsorbate_binding_indices) == 1`.
        - `site_type: "bridge"` must correspond to 1 or 2 binding indices.
        - `site_type: "hollow"` must correspond to 1 or 2 binding indices.

        **3. Other Rules**
        - Strictly forbid proposing adsorption plans with 3 or more adsorbate binding points.
        - If the user requests multi-point adsorption, explain the limitation in `reasoning` and propose a reasonable alternative.
        - Output must be valid JSON and must not contain Markdown fences.
        - The entire process has a hard limit of {max_attempts} attempts.

        **--- Example 1: [C-]#[O+] Adsorption ---**
        {{
          "adsorbate_type": "Molecule",
          "reasoning": "Target is C-ontop bonding. Surface is Cu. Carbon index is 0. Thus surface_binding_atoms is ['Cu'] and adsorbate_binding_indices is [0].",
          "solution": {{
            "action": "continue",
            "site_type": "ontop",
            "surface_binding_atoms": ["Cu"],
            "adsorbate_binding_indices": [0],
            "relax_top_n": 1
          }}
        }}
        **--- End of Example 1 ---**

        **--- Example 2: C=C Adsorption ---**
        {{
          "adsorbate_type": "Molecule",
          "reasoning": "Target is C=C side-on bonding at bridge site. Surface is Pd. Carbon indices are 0 and 1. Thus surface_binding_atoms is ['Pd', 'Pd'] and adsorbate_binding_indices is [0, 1].",
          "solution": {{
            "action": "continue",
            "site_type": "bridge",
            "surface_binding_atoms": ["Pd", "Pd"],
            "adsorbate_binding_indices": [0, 1],
            "relax_top_n": 1
          }}
        }}
        **--- End of Example 2 ---**
        """
    ).strip()
