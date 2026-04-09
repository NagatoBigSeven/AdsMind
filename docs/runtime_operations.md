# Runtime Operations

## Outputs

- Session artifacts are written under `outputs/<session_id>/`.
- Initial placements are stored as `conformers_<smiles>.traj`.
- Relaxation trajectories are stored as `relaxation.traj`.
- Final relaxed candidates are stored as `final.xyz`.
- The current best structure, when one is identified, is exported as `BEST_<smiles>_<site>_E<energy>.xyz`.

## Output Isolation

- The UI generates a short UUID-derived `session_id` for each run.
- Runtime code creates per-session directories before writing files.
- Repeated runs therefore do not overwrite each other's trajectories unless the same `session_id` is reused deliberately.

## Configuration and Secrets

- API keys and the preferred LLM backend are stored in `~/.adsmind/config.json`.
- The legacy `~/.adskrk/config.json` path is still accepted as a fallback.
- Environment variables override values stored in that file.
- The config writer applies a best-effort `0600` permission mask on POSIX systems.

## Performance Controls

- `AGENT_MAX_STEPS` limits graph streaming steps in the Streamlit UI.
- Site sampling is capped to a small subset per site type when symmetric reduction is intentionally disabled for performance.
- `random_seed` can be set to make placement and relaxation behavior reproducible.
- `relaxation_mode=fast` fixes the whole slab and is the default for laptop-friendly runs.
- `relaxation_mode=standard` fixes only the bottom third of the slab and is more physically flexible.

## Operational Caveats

- Heavy local backends such as HuggingFace and MACE inherit the host's PyTorch, accelerator, and driver constraints.
- CI intentionally avoids remote API calls and long relaxation jobs; integration validation should be done on a prepared research machine before publication-quality runs.
- `adsmind-preflight --ci` provides a lightweight local sanity check for install state, backend discovery, and graph compilation.
