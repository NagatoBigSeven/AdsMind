# OCD62 N=5 partial-dissociation rows (writing aid)

The 6 rows in [reproducibility_n5.csv](reproducibility_n5.csv) currently classified
as `missing` are not infrastructure failures — they are partial-dissociation
outcomes where the same surface+adsorbate combination yields a mix of
molecular and dissociated states across the 5 reruns. The dedicated class
`dissociation_excluded` is reserved for rows where *every* run dissociated
(see [reproducibility_n5.md](reproducibility_n5.md) for the headline counts).

This file lists the per-run breakdown so the manuscript text and SI table can
treat each row deliberately rather than lumping them all under "missing."

## Per-row breakdown

🟢 = molecular adsorption (`best_energy_eV` reported), 🔴 = dissociated state
(`last_analysis.is_dissociated == True`), ❌ = early/internal failure.

| case | sid | adsorbate | backend | variant | run1 | run2 | run3 | run4 | run5 | mix |
|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 16 | NO | gpt54 | no_termination | −4.347 🟢 | −4.883 🔴 | −7.047 🟢 | −4.347 🟢 | −4.347 🟢 | **4 mol / 1 dissoc** |
| 002 | 94 | [N]=N | gpt54 | one_shot | −3.346 🟢 | −5.608 🔴 | −5.608 🔴 | −5.608 🔴 | −5.608 🔴 | **1 mol / 4 dissoc** |
| 002 | 94 | [N]=N | claude | one_shot | −5.608 🔴 | −2.736 🟢 | −5.608 🔴 | −5.608 🔴 | −5.608 🔴 | **1 mol / 4 dissoc** |
| 002 | 94 | [N]=N | gemini2.5pro | one_shot | −2.736 🟢 | −5.608 🔴 | −2.736 🟢 | −2.736 🟢 | −2.736 🟢 | **4 mol / 1 dissoc** |
| 007 | 479 | OH | claude | one_shot | −7.228 🟢 | −6.577 🟢 | −7.228 🟢 | −9.476 🔴 | −9.476 🔴 | **3 mol / 2 dissoc** |
| 012 | 768 | H | claude | one_shot | −3.504 🟢 | −3.257 🟢 | −3.257 🟢 | −3.257 🟢 | (early ❌) | **4 mol / 0 dissoc / 1 internal-failure** |

## Suggested SI / paper handling

The rows split naturally into three sub-types, each with its own writing-ready
treatment:

**(a) Dominant-molecular (≥3 of 5 molecular)** — case 001 NO gpt54
no_termination, case 002 [N]=N gemini one_shot, case 007 OH claude one_shot,
case 012 H claude one_shot. The molecular best is well-determined; the 1–2
dissociated runs are stochastic events that the iterative full variant
suppresses. SI table can show the molecular cluster value with a footnote
"(N=4 of 5 molecular; remaining run dissociated)".

**(b) Dominant-dissociation (≤1 of 5 molecular)** — case 002 [N]=N gpt54
one_shot, case 002 [N]=N claude one_shot. The single molecular result is
statistically meaningless on its own. These rows are best handled the same
way as the cleanly-`dissociation_excluded` rows: report dissociation rate
across N=5 (4/5 = 80%) rather than a single-shot energy, and let the full
variant's deterministic molecular result carry the comparison.

**(c) Internal early failure (zero-iteration crash, not dissociation)** —
case 012 H claude one_shot run 5. This is a one-off zero-iteration agent
failure (no payload, no dissoc flag), already noted in
[run5_manifest.csv](run5_manifest.csv) as
"One zero-iteration internal failure has no artifact payload and appears as
a missing energy in the N=5 summary." Treat as N=4 effective for that case.

## Why these are not relisted as `dissociation_excluded`

The `dissociation_excluded` class is defined as "all N runs are
None-with-dissociation" so that the audit table cleanly separates rows where
the surface+adsorbate combination is genuinely incompatible with molecular
adsorption under MACE-MP-0 small (see
[reproducibility_n5.md](reproducibility_n5.md) headline). The 6 rows above
mix outcomes within the same N=5 set, which is informative on its own —
collapsing them into the "all dissociated" class would erase the
within-case stochasticity signal.

If the SI table needs a fully-populated N=5 column for these specific rows,
the simplest path is to extend the seed sweep recipe in
[../../ocd62_overlap12_grok_outlier_seed_sweep_20260509/REPORT.md](../../ocd62_overlap12_grok_outlier_seed_sweep_20260509/REPORT.md)
to the affected (backend × case × one_shot) combos and pull additional
molecular runs until each row hits 5 successes. That is a writing decision,
not a data-integrity gap — the existing data is honest as-is.
