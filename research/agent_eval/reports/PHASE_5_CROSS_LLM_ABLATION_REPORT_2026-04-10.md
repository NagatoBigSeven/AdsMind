# Phase 5 Note: Cross-LLM Ablation Comparison

## Status

Generated a direct Gemini-vs-Grok comparison from the completed 5x5 ablation summaries.

Outputs:

- `research/results/cross_llm_ablation_comparison.csv`
- `research/results/cross_llm_ablation_comparison.json`

Inputs:

- `research/results/gemini_ablation_v1/ablation_summary.csv`
- `research/results/xai_ablation_v2/ablation_summary.csv`

## Overall Result

Across all 25 case-variant rows:

- mean absolute energy difference: `0.1184 eV`
- median absolute energy difference: `0.0 eV`
- exact matches: `15/25`
- within `0.01 eV`: `17/25`
- within `0.05 eV`: `17/25`

Interpretation:

- most Gemini/Grok differences collapse to zero on the completed agentic matrix
- the remaining disagreement is concentrated in a small number of hard rows, not spread uniformly across the benchmark

## By Variant

From `cross_llm_ablation_comparison.json`:

- `full`: mean `|ΔE| = 0.0407 eV`, exact matches `4/5`
- `no_slip`: mean `|ΔE| = 0.0495 eV`, exact matches `3/5`
- `no_forbid`: mean `|ΔE| = 0.0908 eV`, exact matches `3/5`
- `no_termination`: mean `|ΔE| = 0.0867 eV`, exact matches `4/5`
- `single_shot`: mean `|ΔE| = 0.3241 eV`, exact matches `1/5`

Main takeaway:

- iterative search sharply reduces cross-LLM variance
- one-shot behavior is much less backend-stable than the agentic variants

## By Case

- `01`: perfect agreement across all 5 variants
- `02`: nearly identical except `single_shot`, where Gemini is better by `0.6155 eV`
- `09`: agreement on 4/5 rows, with only the `single_shot` row differing by `0.1725 eV`
- `14`: agreement on 4/5 rows, with only the `single_shot` row differing by `0.3716 eV`
- `19`: disagreement on all 5 rows, making it the dominant backend-sensitive stress case

## Largest Disagreements

Top rows by absolute energy difference:

1. `02/single_shot`: `0.6155 eV`
2. `19/single_shot`: `0.4612 eV`
3. `19/no_forbid`: `0.4482 eV`
4. `19/no_termination`: `0.4333 eV`
5. `14/single_shot`: `0.3716 eV`

Interpretation:

- the largest disagreement is not in `full`; it is in `single_shot`
- case `19` remains the primary backend-sensitive system even after the agentic loop is added

## Practical Conclusion

The current data supports a careful but strong claim:

1. agentic search improves not only final energies on hard cases, but also backend robustness
2. Gemini and Grok largely converge under iterative search
3. backend sensitivity is much more visible in single-shot mode and in the hardest case `19`

## What I Need From You

Nothing for this note.

The next useful move is to convert these completed ablation and cross-LLM results into paper-facing tables and prose.
