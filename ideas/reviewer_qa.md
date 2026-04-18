# AdsMind Reviewer Q&A Defense Notes

Anticipated reviewer questions and prepared answers. Not meant for the paper body — internal reference for revision rounds and rebuttal letters.

## Q1. Why does a random baseline beat AdsMind on 4 of 15 cases? Doesn't that invalidate the method?

**Short answer.** Random (N=20) uses 5× more MACE relaxations per case than AdsMind Full (~4). We report this openly in §3.6 (Non-LLM and cross-backend control baselines) and the Discussion. The comparison supports a different claim than "AdsMind finds the deepest energy": it supports "AdsMind gets most of the energy improvement at 5–25× less compute and 100% success rate."

**Longer defense.** The four cases where random wins (04, 16, 18, 20) share a structural feature: complex adsorbates (CH$_2$CH$_2$OH, OCHCH$_3$) on intermetallic surfaces with many competitive binding sites. Random placement seeds multiple trajectories that land in structurally distinct basins; AdsMind's single-trajectory iterative refinement stays in the basin its first relaxation descends into. This is the reliability–depth trade-off we formalize in §4.1 and name explicitly as a negative result.

The multi-seed control experiment (cases 16/17/18, 5 seeds × GPT-5.4, reported in §3.5 Adsorb-Agent comparison and §4.5 Limitations) is the decisive test: even with 20 relaxations matching random's budget, best-of-5-seeds AdsMind is still >1.1 eV worse than Adsorb-Agent on all three cases. So the gap is architectural, not resource-limited.

## Q2. Heuristic enumeration also beats AdsMind on 40% of cases. Is the LLM planner doing anything useful?

The LLM planner is a **compute-efficient approximation of exhaustive enumeration**, not a replacement for it. On the 9/15 cases where both converge to the same minimum (within 0.01 eV), AdsMind uses 1/10 to 1/25 the relaxations. On the 6/15 cases where heuristic wins, the mean gap is 0.48 eV, while heuristic consumes 25–98 relaxations per case. We report this openly in §3.6 as "AdsMind reaches within 0.19 eV of the heuristic optimum at 1/10 to 1/25 the compute."

The value statement is operational: for large-scale screening where relaxations dominate wall-clock, AdsMind delivers the bulk of the energy improvement at a fraction of the MACE budget, with 100% reliability and interpretable reasoning traces. Brute-force methods lack the last two properties.

## Q3. Adsorb-Agent beats AdsMind on 9–10 of 11–12 successful cases. Why present AdsMind at all?

Three reasons:

1. **Reliability.** Adsorb-Agent fails on 4/15 cases with GPT-4o (27%) and 3/15 with GPT-5.4 (20%). Failure patterns differ by LLM, which means the failure mode is architectural (single-pass planning) not a capability artifact. AdsMind is 100% reliable across all 4 backends × 25 cases (300+200 runs).
2. **Compute.** Adsorb-Agent uses ~21 MACE relaxations per case vs AdsMind's ~4. Compute-matched bootstrap (Adsorb-Agent subsampled to 4 relaxations per case) confirms the gap collapses: case 16 shifts from a 2.04 eV deficit to 48% AdsMind win rate. So depth depends on sampling, not planning.
3. **Interpretability.** Adsorb-Agent's single-pass architecture emits no diagnostic signal for failed cases — the reviewer cannot distinguish "no low-energy site exists" from "LLM predicted the wrong site type." AdsMind's slip events and FORBID constraints are physically grounded artifacts that a practitioner can inspect.

The honest summary: Adsorb-Agent wins on depth when it doesn't fail. AdsMind wins on reliability, efficiency, and interpretability. Different methods for different operating conditions.

## Q4. Is Chemical Slip validated as an LLM evaluation metric?

Within-paper validation: slip rate stratifies cleanly by surface complexity across 4 independent LLM backends on 300 CMU runs (§3 slip analysis). The monometallic-vs-intermetallic gradient is consistent across Gemini, Grok-4, GPT-5.4, and Claude, which rules out LLM-specific artifacts.

Claim calibration: we position slip as a "standalone methodological contribution" (Discussion §4.2), not as a validated LLM benchmark. Full validation against independent benchmarks (ChemBench, MatBench) is future work.

## Q5. The MACE-MP-0 small, CPU, float32 backend is not production-grade. Do conclusions change under higher-fidelity force fields?

Partially. The MACE-large sensitivity analysis (§3.6 MACE-large sensitivity paragraph; §4.4 MLFF as surrogate) on 5 representative cases shows:

- Energy ordering AdsMind vs Adsorb-Agent preserved on all 5 cases.
- Cross-backend convergence pattern preserved.
- Absolute gap narrows substantially: case 16 from 2.04 → 0.97 eV, case 18 from 1.35 → 0.39 eV.

So some of the apparent MACE-small depth gap is force-field artifact, not genuine search-strategy difference. We state this honestly in the Discussion. DFT validation is in progress through the chemistry collaborator (Bowen Zhang, HKUST).

## Q6. With 15 cases on CMU and 10 on OCD-GMAE, can you really make strong claims?

Friedman tests reach significance on all 4 backends across both benchmarks (min p = 0.011 on CMU, 3.4e-4 on OCD-GMAE). Pairwise Wilcoxon tests survive BH correction for Full vs 1-Shot on 3/4 backends on CMU. We interpret individual comparisons primarily through effect sizes and bootstrap 95% CIs, and rely on consistency of direction across 4 independent LLMs as a form of conceptual replication.

The design intent is to isolate effects robustly with limited cases, not to maximize statistical power. The 4-backend × 2-dataset × 5-variant factorial design provides 40 independent conditions per claim. Consistency of effect sign across this matrix is the evidence, not any single p-value.

## Q7. Why not add more ablation experiments (e.g., ablating individual LLM reasoning steps)?

Scored 75/100 earlier in the review process. The key remaining gaps are (i) DFT validation (costly, handled by collaborator), (ii) validation on a larger third benchmark (would add 6–12 weeks of compute), and (iii) adaptive/soft FORBID variants (future work). We ran the necessary controls:

- Random N=20 baseline (compute-anchored)
- Heuristic enumeration baseline (Autoadsorbate, no LLM)
- Adsorb-Agent GPT-4o (same-architecture different-LLM)
- Adsorb-Agent GPT-5.4 (matched-LLM control)
- Iteration convergence analysis (mechanistic)
- MACE-large sensitivity (force-field dependence)
- Multi-seed control (resource-limited vs architectural)
- OCD-GMAE independent validation (300 → 500 runs)

Further experiments have diminishing returns given the clarity of the reliability–depth trade-off conclusion.

## Q8. How sure are you the cross-backend convergence reflects physical truth rather than shared LLM training data?

Strong: the four LLMs were trained by four independent organizations on different corpora with different post-training regimes. Post-Full convergence to a 0.129 eV range (CMU) from a 0.425 eV one-shot spread is a 3.3× reduction that cannot be explained by training-data overlap — if shared priors were driving the result, one-shot would already be tight.

The mechanism we propose is that closed-loop iteration grounds each backend in the same MACE physical signal, so different initial LLM priors are updated toward the same physical minimum. This is testable: swapping to a different MLFF should shift the convergence basin but preserve the convergence pattern, which is what we see in the MACE-large ablation.

## Q9. Is this just MACE doing the work? What role does the LLM actually play?

The 1-Shot control answers this directly. 1-Shot uses identical MACE physics with a single LLM placement; the four-backend range on CMU is 0.425 eV. Under Full (iterative LLM feedback + MACE), the range collapses to 0.129 eV. The difference cannot be attributed to MACE since the force field is held fixed across conditions.

Additionally, the random baseline shows that naive sampling with MACE, even at 5× the budget, does not converge to the Full result — it finds a different (usually lower) basin on complex cases. The LLM's role is basin selection at iteration 1 and course correction at iterations 2–4; MACE's role is accurate local refinement.

## Q10. Why should a chemist trust this agent for real catalyst design?

Short answer: for screening, not. For autonomous exploration of a candidate surface where a human-in-the-loop would be too slow, yes — subject to the operating envelope we specify (flat and stepped crystalline surfaces, single adsorbate species, MLFF-addressable bonding physics). The closed-loop architecture's 100% reliability and interpretable slip/FORBID traces are specifically the properties that distinguish it from single-pass alternatives for autonomous workflows.

The intended integration pattern we outline in §4 is a two-stage pipeline: brute-force screening (heuristic enumeration) to select promising candidates, closed-loop AdsMind refinement on top candidates for interpretable characterization and reliable convergence. This combines depth with reliability.

## Q11. Reproducibility: how sensitive is this to LLM API version changes?

Discussed explicitly in §4.5 (Limitations). At temperature 0.0 the outputs may still vary across API versions (providers update without notice). We mitigate by:

1. Recording exact model version identifiers in every run log.
2. Releasing full prompt templates as SI.
3. Releasing complete trajectory logs for all 500 runs so any reported result can be re-verified against saved data.
4. Using 4 independent backends to ensure conclusions do not hinge on a single provider.

The cross-machine control experiment (EPFL x86_64 vs M3 Pro ARM) documents a ~0.20 eV platform shift on case 14 that is MLFF-environment-driven, not LLM-driven. All within-backend ablation comparisons in the main text use a single platform throughout.

## Q12. What's the DFT comparison?

In progress via collaborator Bowen Zhang (HKUST chemistry). Not in this submission. We acknowledge this as a scope limitation in §4.4 (MLFF as surrogate) and commit to reporting DFT validation in a follow-up. The MACE-large sensitivity analysis is the strongest within-paper evidence that rankings are preserved across force-field fidelity.

## Q13. The paper now explicitly states random/heuristic win on several cases. Isn't this weakening your own paper?

No — it strengthens it by making the claim falsifiable and precise. The previous framing ("AdsMind finds better energies") would have been attacked by any reviewer who ran the random baseline. By acknowledging the reliability–depth trade-off up front, we make the contribution surgical: closed-loop LLM reasoning adds value for *reliability, compute efficiency, and interpretability*, which together enable autonomous workflows — a different axis than brute-force depth.

Reviewers respect papers that are honest about limitations. The four-claim C1–C4 structure in §1.5 makes explicit what the paper does and does not prove; readers can evaluate each claim independently.

## Q14. Why Vertex AI direct for Gemini instead of AiHubMix (used in previous runs)?

AiHubMix proxy exhibited systematic artifacts in early Gemini runs (observed during plan verification 2026-03 to 2026-04). Vertex AI direct eliminates the proxy layer and is the primary Gemini access method for the OCD-GMAE V2 data used in the paper tables. The CMU data was re-audited and was not affected. This is documented in the OCD-GMAE paper tables file header and referenced in §3.4 of Results (Independent validation on OCD-GMAE).

---

Last updated: 2026-04-18 (section-number audit + Autoadsorbate citation corrected to Fako \& De 2025).
Contact for rebuttal drafting: Zongmin Zhang (first author, aq717061@gmail.com).
