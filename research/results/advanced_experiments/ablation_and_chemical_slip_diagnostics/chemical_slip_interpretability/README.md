# Chemical Slip Interpretability

CMU20 diagnostic tables for how planned adsorption sites relax under the
MACE-MP-0 small protocol.

- `cmu20/slip_analysis.csv`: one-shot planned-site versus relaxed-site labels
  for Gemini and Grok, plus case metadata. This is the compact table used for
  the Gemini/Grok slip-agreement diagnostic.
- `cmu20/slip_analysis.json`: aggregate slip rates by backend and surface
  family. The JSON also includes GPT-5.4 and Claude aggregate rates.
- `cmu20/case19_trajectory.csv`: case-19 per-attempt trajectory across all four
  LLM backends and all five variants.
- `cmu20/case19_trajectory.json`: detailed record behind the case-19 trajectory
  table.

These files are interpretability diagnostics derived from the CMU20 basic
experiment matrix; they are not an additional dataset.
