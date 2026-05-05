# Questions To Answer (QTA) - Methods Section

**Generated**: 2026-05-04  
**Purpose**: Track unresolved questions from Methods section review  
**Status**: Pending author response

---

## 🔴 High Priority (Affect Scientific Integrity)

### Q1: System Input Description Incomplete
**Location**: L9-10  
**Problem**: The minimal input description is incomplete. Reader doesn't know what parameters are required vs. optional.

**Questions**:
- Is "request prompt" a natural-language instruction? What format?
- Are there optional parameters (max iterations, force threshold, forbidden sites)?
- Should we list all input parameters explicitly for reproducibility?

**Suggested Answer** (for reference):
> "The minimal input consists of three elements: (1) a natural-language task description, (2) the adsorbate SMILES string, and (3) the surface slab in ASE-compatible format. Optional parameters include maximum iteration budget (default: 5), force convergence threshold $f_{\text{max}}$ (default: 0.05 eV/Å), and forbidden site patterns."

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer

---

### Q2: γ Parameter Hard Threshold Lacks Physical Justification
**Location**: L68  
**Problem**: The threshold $E_{\text{ads}} < -0.5$ eV for relaxing γ from 1.30 to 1.45 is a hard cutoff without explanation. This may cause discontinuities in bond detection.

**Questions**:
- How was -0.5 eV chosen? Based on chemical intuition or dataset statistics?
- Why not use a smooth transition (e.g., sigmoid function)?
- Should we cite prior work that defines "strong adsorption" as $E_{\text{ads}} < -0.5$ eV?

**Suggested Answer** (for reference):
> "The threshold $E_{\text{ads}} < -0.5$ eV follows the convention in surface science that chemisorbed states typically exhibit adsorption energies below -0.5 eV [cite relevant work]. This heuristic is validated in Section SX (SI) where we show that γ=1.45 improves coordination number accuracy for strongly adsorbed states by 15% compared to γ=1.30."

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer / 📊 Provide data reference

---

### Q3: Ablation Variant Selection Lacks Justification
**Location**: L92-100  
**Problem**: Five variants (Full, w/o Slip, w/o Forbid, w/o Term, 1-Shot) are listed without explaining why these specific five were chosen. Reader may not understand the conceptual differences between "Slip" and "Forbid".

**Questions**:
- Why these five? Why not test "w/o Slip + w/o Forbid" as a combined variant?
- What is the conceptual difference between Slip and Forbid? (Slip = detection, Forbid = enforcement?)
- Should we add a sentence explaining the ablation logic?

**Suggested Answer** (for reference):
> "The five variants decompose the contributions of three mechanisms: (1) Slip feedback provides detection and guidance, (2) Forbid constraint enforces negative constraints, and (3) Termination enables early stopping. The w/o Slip variant tests whether slip detection alone (without guidance) is sufficient; the w/o Forbid variant tests whether guidance alone (without explicit prohibition) is sufficient. The 1-Shot variant provides a lower bound by disabling all mechanisms."

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer

---

### Q4: Tier 3 Case Selection Criteria Opaque
**Location**: L128-130  
**Problem**: "selected 12 cases from Tier 2" doesn't explain the selection methodology. Reader cannot reproduce the selection.

**Questions**:
- Are the 12 cases randomly sampled? Stratified sampling? Selected based on energy variance?
- What criteria ensure "surface-adsorbate diversity"?
- Should we list the 12 cases explicitly in the paper or SI?

**Suggested Answer** (for reference):
> "The 12 cases are selected by stratified sampling to preserve the surface-adsorbate diversity of the Tier 2 set: 4 monometallic surfaces, 4 intermetallic surfaces, and 4 compound surfaces, each with one small adsorbate (H or OH) and one large adsorbate. This selection ensures that variance estimates generalize across surface types and adsorbate sizes."

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer / 📋 Provide case list

---

## 🟡 Medium Priority (Affect Clarity and Completeness)

### Q5: "Two-Step Evaluation" Description Incomplete
**Location**: L42-43  
**Problem**: L34-37 describes pre-processing (surrogate-SMILES layer), which should be "Step 1", but L42 says "A two-step evaluation procedure is then employed" (referring to screening + relaxation). This creates confusion about whether the procedure is 2-step or 3-step.

**Questions**:
- Should we rephrase as "three-step" (pre-processing → screening → relaxation)?
- Or should we explicitly state that pre-processing is conditional and not counted as a "step"?

**Suggested Answer** (for reference):
> "A **three-stage evaluation procedure** is employed. First, the proposal is pre-processed by the surrogate-SMILES geometry layer (Section 2.2.1). Second, candidate structures are screened with the MACE-MP calculator to discard pathological configurations. Third, the best surviving candidate is fully relaxed and analyzed."

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer

---

### Q6: Surrogate-SMILES Geometry Layer Description Insufficient
**Location**: L37-40  
**Problem**: The mapping from SMILES to 3D coordinates is a core technical contribution, but only 4 lines are dedicated to it. Reader cannot understand how "proxy adsorption markers" work.

**Questions**:
- What are "proxy adsorption markers"? Virtual atoms? Special SMILES tokens?
- How are 8 surface coordinates × 4 conformers selected? What is the "capped set"?
- Should we add a reference to SI for full algorithm details?

**Suggested Answer** (for reference):
> "The surrogate-SMILES layer maps the adsorbate SMILES to an initial 3D pose by (1) identifying the binding atom(s) from the Planner's hypothesis, (2) placing proxy adsorption markers (virtual atoms that mimic surface binding sites) at the binding atom coordinates, and (3) generating conformers with RDKit. The 8 surface coordinates are selected by filtering the surface for the requested site type and surface-symbol pattern, then ranking by a heuristic score (distance to surface center). The 4 conformers per site are generated by RDKit's ETKDG algorithm with diverse randomization seeds."

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer / 📎 Add SI reference

---

## 🟢 Low Priority (Minor Issues)

### Q7: "Standard Mode" Implies Non-Standard Mode Exists
**Location**: L59  
**Problem**: "In the standard mode, the bottom fraction..." implies there is a non-standard mode, but this is never explained.

**Questions**:
- Is there a non-standard mode? If not, change to "By default"?
- If yes, should we describe it in SI?

**Suggested Answer** (for reference):
> Change "In the standard mode" to "By default" (if only one mode exists).

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer

---

### Q8: LLM Backend List Redundancy Not Fully Resolved
**Location**: L102 vs L133  
**Problem**: In the modified version, L102 still contains the detailed LLM backend list (Gemini~2.5~Pro, Grok-4, etc.), while L133 now references Section 2.4. This creates mild redundancy.

**Questions**:
- Should we delete the detailed list at L102 and replace with "Four reasoning backends are evaluated (see Table S1 for model identifiers)"?
- Or keep L102 and delete the reference at L133?

**Suggested Answer** (for reference):
> Keep the detailed list at L102 (since Section 2.4 is about evaluation protocol, not backend details). Delete the reference at L133 and keep the current text ("All experiments use the four LLM backends listed in Section 2.4" is sufficient).

**Action Required**: ✅ Accept suggested answer / ✏️ Provide custom answer

---

## 📊 Summary

| Priority | Question ID | Status | Action |
|----------|-------------|--------|--------|
| 🔴 High | Q1: System input | ⏳ Pending | Provide input parameter list |
| 🔴 High | Q2: γ threshold | ⏳ Pending | Provide physical justification or cite prior work |
| 🔴 High | Q3: Ablation variants | ⏳ Pending | Add 1-2 sentence justification |
| 🔴 High | Q4: Tier 3 selection | ⏳ Pending | Provide selection methodology |
| 🟡 Medium | Q5: Two-step vs three-step | ⏳ Pending | Clarify procedure stages |
| 🟡 Medium | Q6: Surrogate-SMILES | ⏳ Pending | Add detail or SI reference |
| 🟢 Low | Q7: "Standard mode" | ⏳ Pending | Change to "By default" |
| 🟢 Low | Q8: LLM list redundancy | ⏳ Pending | Decide which list to keep |

---

## ✅ Next Steps

1. **Author reviews QTA.md**
2. **For each question, choose one of**:
   - ✅ Accept suggested answer (I will implement)
   - ✏️ Provide custom answer (Author provides text)
   - 📊 Provide data reference (Author points to data file)
   - 📎 Add SI reference (Author agrees to add detail in SI)
3. **Return QTA.md with answers**
4. **I implement all accepted suggestions**

---

**Files modified**:
- `/Users/lixuecheng/Documents/ai4qc/AdsMind/overleaf/sections/2_Method.tex` (8 modifications completed)

**Files created**:
- `/Users/lixuecheng/Documents/ai4qc/AdsMind/overleaf/QTA.md` (this file)

---

**Notes**:
- Questions are sorted by priority (High → Medium → Low)
- Each question includes suggested answer for reference
- Author can edit suggested answers or provide custom answers
- After QTA resolution, we should update `OCD-GMAE62 合并修改清单.md`
