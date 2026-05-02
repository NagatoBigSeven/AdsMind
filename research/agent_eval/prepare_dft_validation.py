"""Compatibility wrapper for legacy_prepare_topk_dft_handoff.

Use `python -m research.agent_eval.export_dft_iteration_alignment` for the
current per-iteration DFT-alignment workflow.
"""

from research.agent_eval.legacy_prepare_topk_dft_handoff import *  # noqa: F401,F403
from research.agent_eval.legacy_prepare_topk_dft_handoff import main


if __name__ == "__main__":
    raise SystemExit(main())
