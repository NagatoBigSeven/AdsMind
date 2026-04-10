# CMU Benchmark SMILES Resolution

This document records the best-available SMILES reconstruction for the 20
benchmark systems used by AdsMind. It is the Phase 0 input contract for all
subsequent agent-side experiments.

## Evidence Sources

- Manual run logs under [`logs/`](/Users/nagato/workspace/AdsMind/logs) for cases 3-19
- Adsorb-Agent example configs under
  [`CatalystAIgent/config/example/`](/Users/nagato/workspace/AdsMind/CatalystAIgent/config/example)
- Previous AdsMind artifacts under
  [`results/`](/Users/nagato/workspace/AdsMind/results)
- AdsMind filename sanitization rules in
  [`src/tools/common.py`](/Users/nagato/workspace/AdsMind/src/tools/common.py)

## Resolution Rules

- `sanitize_smiles_for_filename()` replaces `=` and `#` with `_`, and can strip
  `[` / `]`.
- Cases 3-19 are locked to the exact command lines recovered from
  [`logs/`](/Users/nagato/workspace/AdsMind/logs).
- Cases 1-2 remain reconstructed from prior local results because their logs are
  lost.
- For cases 15-20, benchmark execution is locked to the recovered AdsMind
  inputs, while documentation keeps an explicit "paper label still to be
  reconciled" note.

## Resolved Table

| Case | Surface | Paper Adsorbate Label | Resolved SMILES | Confidence | Evidence |
|------|---------|------------------------|-----------------|------------|----------|
| 01 | Mo3Pd(111) | H | `[H]` | High | Previous filenames and plan; atomic H |
| 02 | Mo3Pd(111) | NNH | `[N]=[NH]` | High | Previous filenames and plan |
| 03 | CuPd3(111) | H | `[H]` | High | Previous filenames and plan |
| 04 | CuPd3(111) | NNH | `[N]=[NH]` | High | Previous filenames and plan |
| 05 | Cu3Ag(111) | H | `[H]` | High | Previous filenames and plan |
| 06 | Cu3Ag(111) | NNH | `[N]=[NH]` | High | Previous filenames and plan |
| 07 | Ru3Mo(111) | H | `[H]` | High | Previous filenames and plan |
| 08 | Ru3Mo(111) | NNH | `[N]=[NH]` | High | Previous filenames and plan |
| 09 | Pt(111) | OH | `[OH]` | High | ORR example + previous filenames |
| 10 | Pt(100) | OH | `[OH]` | High | Previous filenames and plan |
| 11 | Pd(111) | OH | `[OH]` | High | Previous filenames and plan |
| 12 | Au(111) | OH | `[OH]` | High | Previous filenames and plan |
| 13 | Ag(100) | OH | `[OH]` | High | Previous filenames and plan |
| 14 | CoPt(111) | OH | `[OH]` | High | Previous filenames and plan |
| 15 | Cu6Ga2(100) | CH2CH2OH | `[CH2]CO` | High for prior AdsMind run | `generated_conformers_[CH2]CO.traj`; formula `C2H5O`; sanitization matches |
| 16 | Au2Hf(102) | CH2CH2OH | `[CH2]CO` | High for prior AdsMind run | Same as case 15 |
| 17 | Rh2Ti2(111) | OCHCH3 | `CC=O` | High for AdsMind reproducibility / medium-high for paper alignment | `logs/17.txt` command line + `generated_conformers_CC_O.traj`; formula `C2H4O`; `=` becomes `_` |
| 18 | Al3Zr(101) | OCHCH3 | `CC=O` | High for AdsMind reproducibility / medium-high for paper alignment | `logs/18.txt` + same artifact pattern as case 17 |
| 19 | Hf2Zn6(110) | OCHCH3 | `CC=O` | High for AdsMind reproducibility / medium-high for paper alignment | `logs/19.txt` + same artifact pattern as case 17 |
| 20 | Bi2Ti6(211) | ONN(CH3)2 | `CN(C)N=O` | Medium | Top-level `generated_conformers_CN(C)N_O.traj`; formula `C2H6N2O`; `=` becomes `_`; case directory is empty |

## Important Caveats

1. Cases 15-20 are resolved to the **actual previous AdsMind inputs** recoverable
   from local logs/artifacts.
2. Cases 15-20 follow a dual-track policy:
   - benchmark runs use the recovered AdsMind SMILES above
   - documentation keeps an explicit note that the paper label may still need
     reconciliation against missing upstream metadata
3. Case 20 has a special archival issue:
   - [`results/20`](/Users/nagato/workspace/AdsMind/results/20) is empty
   - but case-specific artifacts exist at the top level of
     [`results/`](/Users/nagato/workspace/AdsMind/results)
4. Until external confirmation is available, all new batch runs should use the
   resolved SMILES above to stay consistent with the existing local evidence.
