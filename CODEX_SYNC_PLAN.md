# Codex Task: Overleaf ↔ Local Paper Sync

## Background (read first)

Two LaTeX drafts have diverged in this repo:

- `paper/` — Zongmin (first author) local draft. More complete on Intro, Results, Discussion, SI, refs.
- `overleaf/` — snapshot of Lou Yuyang's Overleaf project (zip-downloaded 2026-04-20, **no git integration**). Skeleton / half-finished. Method section is more expanded than local.

The final target: `overleaf/` becomes the **single source of truth** for paper content. Division of labor going forward is:
- **Lou Yuyang** → figures, captions, formatting, color
- **Zongmin** → facts, data, narrative

Before that division can work, we must land all the more-complete local content into `overleaf/` *without clobbering* sections where Lou genuinely improved the prose (notably Method).

### Already applied to `paper/` — 7 fact fixes that MUST land in the merged `overleaf/`

1. `paper/sections/2_Method.tex:24` — 5-case stale description → 15-case
2. `paper/sections/3_Results.tex:16` — case 12/15 single-shot claim qualified
3. `paper/sections/3_Results.tex:30` — Grok-4 $-$Term "14/15" → "13/15 strict (14/15 within 0.01 eV)"
4. `paper/sections/3_Results.tex:110` — heuristic median "47 sites" → "53 sites"
5. `paper/sections/3_Results.tex:115` — $\Delta = -2.08$ eV → $-2.07$ eV
6. `paper/sections/3_Results.tex:122` — 0.66 eV → 0.65 eV gap
7. `research/results/si4_ocd_gmae_ablation_statistics.tex` — 6 Max degr. cells corrected (Grok-4 $-$Slip/Forbid/Term + Claude $-$Slip/Forbid/Term)

### Out of scope (do not touch)
- `research/results/*.csv`, `*.json` — authoritative data
- `research/results/*.tex` — SI table fragments, already verified
- `overleaf/old_version/` — Springer Nature template bloat
- Any file outside `paper/`, `overleaf/`

---

## Phase 1 — Diff & Classify (this task). DO NOT WRITE TO overleaf/ OR paper/ YET.

### Files to compare

| Overleaf | Local | Pre-inspection note |
|---|---|---|
| `overleaf/main_new.tex` (109 L) | `paper/main.tex` (113 L) | Overleaf's abstract is empty and missing `\input` for Discussion/Conclusion |
| `overleaf/sections/1_Introduction.tex` (51 L) | `paper/sections/1_Introduction.tex` (84 L) | local fuller |
| `overleaf/sections/2_Method.tex` (75 L) | `paper/sections/2_Method.tex` (24 L) | **overleaf fuller** — Lou expanded |
| `overleaf/sections/3_Results.tex` (92 L) | `paper/sections/3_Results.tex` (146 L) | local fuller + has 7 fact fixes |
| `overleaf/sections/4_DiscussionConclusion.tex` (1 L) | `paper/sections/4_DiscussionConclusion.tex` (91 L) | overleaf **empty** |
| `overleaf/sections/5_Data_Availability.tex` | `paper/sections/5_Data_Availability.tex` | both 1 line |
| `overleaf/si.tex` (130 L) | `paper/si.tex` (155 L) | local fuller |
| `overleaf/refs.bib` (25 L) | `paper/refs.bib` (145 L) | local has far more entries |

### For each file pair, produce

A per-block classification where a "block" = one paragraph, one `\section`/`\subsection` chunk, or one logical unit (e.g., one `\begin{enumerate}...\end{enumerate}`). Use these labels:

| Label | Meaning | Merge action (Phase 2) |
|---|---|---|
| `IDENTICAL` | same content in both | no-op |
| `OVERLEAF_ONLY` | exists only in overleaf | keep in merged |
| `LOCAL_ONLY` | exists only in local | add to merged |
| `OVERLEAF_BETTER` | both have it, Lou's version reads better / is more current | keep overleaf's |
| `LOCAL_BETTER` | both have it, local has more content / fixed facts / more accurate numbers | replace overleaf's with local's |
| `NEEDS_HUMAN` | genuine conflict or stylistic judgment call | flag for Zongmin |

### Judgment rules

- **Numerical claims, case counts, statistics, citations** → local wins (paper/ has the 7 verified fact fixes and matches research/results/ CSVs).
- **Prose polish, sentence flow, structural reordering** → if Lou clearly improved readability without changing facts, `OVERLEAF_BETTER`.
- **Missing abstract, missing Discussion, missing refs** → `LOCAL_ONLY`.
- **Method section expansion** → likely `OVERLEAF_BETTER` (Lou added 51 lines). BUT: read carefully. If the expansion contradicts the Results section or the 7 fact fixes, flag `NEEDS_HUMAN`.
- When unsure, mark `NEEDS_HUMAN`. Do not guess.

### Special handling

1. **`main_new.tex` / `main.tex`**: the merged main should keep filename `main_new.tex` (Lou's) and must:
   - Fill in abstract from local
   - Add `\input{sections/4_DiscussionConclusion}` (currently missing around L90)
   - Flag Acknowledgements placeholder ("EPFL funding?") as `NEEDS_HUMAN`
   - Preserve Lou's `\sherry{}` / `\yuyang{}` tracking macros (L37-38)
2. **`refs.bib`**: list all keys in each version. Then run `rg '\\cite\{[^}]+\}' overleaf/sections/*.tex overleaf/main_new.tex` to extract every cite key actually used. Any key cited but missing from overleaf/refs.bib → `MUST_ADD`.
3. **`si.tex`**: the SI currently uses `\input{../research/results/si_...}` paths. In the local `paper/si.tex` these resolve (paper/ and research/ are siblings). In Overleaf cloud, the file layout will be flat — **flag this path question as an open issue in the report**, do not resolve it yet.

### Output

Write **one file**: `OVERLEAF_SYNC_REPORT.md` at repo root. Structure:

```
# Overleaf Sync — Phase 1 Report

## TL;DR
- N blocks classified
- X need human review
- Y local-only blocks to push to overleaf
- Z overleaf-better blocks to preserve

## File: main_new.tex
(summary + per-block table)

## File: sections/1_Introduction.tex
(summary + per-block table with columns: block_id | summary | label | justification)

...

## refs.bib analysis
- overleaf keys (N): [...]
- local keys (M): [...]
- cited in overleaf/*.tex: [...]
- MUST_ADD: [...]

## Open issues for Zongmin
- si.tex input paths (flat vs nested)
- Acknowledgements placeholder
- ...any NEEDS_HUMAN items with context

## Proposed Phase 2 execution order
(ordered list of file merges, safest first)
```

Use GitHub-flavored markdown tables. Keep each justification to one line. No emojis.

### Stop conditions

- Do **not** modify any file under `overleaf/` or `paper/`.
- Do **not** touch `research/results/`.
- Do **not** create the merged files yet.
- After writing the report, stop and return a 3–5 line summary to Zongmin.

---

## Phase 2 — Merge execution

Specified separately after Zongmin reviews Phase 1. At that point Codex will:
- Apply the approved classifications to produce the merged `overleaf/` tree
- Verify the 7 fact fixes landed
- Write a one-screen changelog for Zongmin to paste to Lou
- Not touch Overleaf cloud — upload is manual (web UI drag-drop per file)
