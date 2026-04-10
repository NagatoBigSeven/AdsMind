# Phase 4 Interim: Gemini 5x5 Ablation Matrix

## Status

Phase 4 is currently running.

Active output root:

- `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1`

Completed so far:

- `full/01`
- `full/02`
- `full/09`
- `full/14`
- `full/19`
- `no_slip/01`
- `no_slip/02`
- `no_slip/09`
- `no_slip/14`
- `no_slip/19`
- `no_forbid/01`
- `no_forbid/02`
- `no_forbid/09`
- `no_forbid/14`
- `no_forbid/19`

In progress when this interim note was updated:

- `no_termination/01`

Not started yet:

- `no_termination/02`
- `no_termination/09`
- `no_termination/14`
- `no_termination/19`
- all `single_shot`

## Completed Results So Far

### full/01

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/full/01/result.json`
- best energy: `-3.6317179203033447 eV`
- iterations: `5`
- chemical slips: `4`

Interpretation:

- The run used the full attempt budget.
- Multiple replanning cycles occurred.
- The best energy matches the previously observed strong Gemini/Grok full-search behavior for case `01`.

### full/02

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/full/02/result.json`
- best energy: `-4.765958786010742 eV`
- iterations: `4`
- chemical slips: `3`

Interpretation:

- This is already a strong positive agentic result.
- Compared with Gemini one-shot (`-4.333539962768555 eV`), the full agent improved by roughly `-0.4324 eV`.
- The planner terminated early after convergence logic, rather than blindly consuming all 5 attempts.

### full/09

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/full/09/result.json`
- best energy: `-1.9739322662353516 eV`
- iterations: `3`
- chemical slips: `1`

Interpretation:

- Full search improved over Gemini one-shot (`-1.8013858795166016 eV`) by roughly `-0.1725 eV`.
- This case did not require the full 5-attempt budget.

### full/14

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/full/14/result.json`
- best energy: `-3.6166324615478516 eV`
- iterations: `5`
- chemical slips: `4`

Interpretation:

- This is another strong positive full-search case.
- Compared with Gemini one-shot (`-3.2451114654541016 eV`), the improvement is roughly `-0.3715 eV`.

### full/19

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/full/19/result.json`
- best energy: `-3.8413848876953125 eV`
- iterations: `5`
- chemical slips: `3`

Interpretation:

- This case is important because it breaks the “full is always better” pattern.
- Compared with Gemini one-shot (`-4.029319763183594 eV`), full search is worse by roughly `+0.1879 eV`.
- The run also produced dissociation events during search, which were rejected in favor of the non-dissociated best result.

### no_slip/01

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_slip/01/result.json`
- best energy: `-3.6317179203033447 eV`
- iterations: `5`
- chemical slips: `4`

Interpretation:

- On case `01`, removing slip feedback text did not degrade the final best energy.
- At least for this case, the search still recovered the same best structure as `full`.

### no_slip/02

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_slip/02/result.json`
- best energy: `-4.765775680541992 eV`
- iterations: `5`
- chemical slips: `5`

Interpretation:

- This is the first strong sign that slip feedback may not be the dominant factor on every difficult case.
- Despite removing slip guidance, the run nearly matched `full/02` (`-4.765958786010742 eV`).
- That weakens any simplistic claim that “slip feedback alone” explains the agentic gain on case `02`.

### no_slip/09

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_slip/09/result.json`
- best energy: `-1.9739322662353516 eV`
- iterations: `3`
- chemical slips: `1`

Interpretation:

- This exactly matches `full/09`.
- On this case, removing slip feedback text has no observable effect on the final best energy.

### no_slip/14

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_slip/14/result.json`
- best energy: `-3.6166324615478516 eV`
- iterations: `5`
- chemical slips: `3`

Interpretation:

- This exactly matches `full/14` on best energy.
- The search trajectory differs slightly in slip count, but not in the final outcome.

### no_slip/19

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_slip/19/result.json`
- best energy: `-3.8413848876953125 eV`
- iterations: `5`
- chemical slips: `3`

Interpretation:

- This exactly matches `full/19`.
- On the current representative set, case `19` remains the counterexample where full-style multi-attempt search does not beat one-shot, but removing slip text does not change that fact either.

### no_forbid/01

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_forbid/01/result.json`
- best energy: `-3.6317179203033447 eV`
- iterations: `5`
- chemical slips: `4`

Interpretation:

- This exactly matches `full/01`.
- Removing `FORBID` guidance does not affect the final best energy on this case.

### no_forbid/02

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_forbid/02/result.json`
- best energy: `-4.765714645385742 eV`
- iterations: `5`
- chemical slips: `5`

Interpretation:

- This nearly matches `full/02` (`-4.765958786010742 eV`).
- The search still recovers the strong low-energy solution even without explicit `FORBID` text.
- Slip count rises relative to `full`, but final energy does not materially degrade.

### no_forbid/09

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_forbid/09/result.json`
- best energy: `-1.9739322662353516 eV`
- iterations: `3`
- chemical slips: `1`

Interpretation:

- This exactly matches `full/09`.

### no_forbid/14

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_forbid/14/result.json`
- best energy: `-3.6166324615478516 eV`
- iterations: `5`
- chemical slips: `2`

Interpretation:

- This exactly matches `full/14` on final energy.
- It reaches the same best energy with fewer recorded slips than `full`.

### no_forbid/19

- result: `/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/no_forbid/19/result.json`
- best energy: `-4.042137145996094 eV`
- iterations: `5`
- chemical slips: `5`

Interpretation:

- This is the first case where removing `FORBID` improves over `full`.
- Compared with `full/19` (`-3.8413848876953125 eV`), `no_forbid` is better by roughly `-0.2008 eV`.
- That weakens any blanket claim that `FORBID` guidance is universally beneficial.

## Current Working Conclusion

Even before the full matrix completes, Gemini already shows the same high-value pattern previously seen with Grok-4:

- difficult cases like `02` benefit materially from multi-attempt search
- the runtime is genuinely exercising slip handling, FORBID guidance, replanning, and termination
- the ablation matrix is producing real agentic traces, not just configuration-level no-ops
- full search is not uniformly beneficial: `19` is currently a counterexample
- slip feedback is not yet isolated as the sole driver, because the completed `no_slip` runs are effectively indistinguishable from `full` on final energy
- FORBID guidance is also not uniformly beneficial, because the completed `no_forbid` runs mostly match `full` and even outperform it on `19`

## Next Milestone

The next useful checkpoint is:

- complete `no_termination`
- then compare `full` vs `no_termination` case-by-case before moving to the final `single_shot` completion pass

At the current checkpoint, the Gemini `full` vs Gemini `one-shot` summary over the five representative cases is:

- better in `4/5`
- worse in `1/5`
- mean delta `-0.1708 eV`
- median delta `-0.1725 eV`

At the current checkpoint, the Gemini `no_slip` vs Gemini `full` summary over the same five representative cases is:

- worse in `1/5`
- tied in `4/5`
- better in `0/5`
- mean delta `+0.0000366 eV`
- median delta `0.0 eV`

At the current checkpoint, the Gemini `no_forbid` vs Gemini `full` summary over the same five representative cases is:

- better in `1/5`
- tied in `3/5`
- worse in `1/5`
- mean delta `-0.0401 eV`
- median delta `0.0 eV`
