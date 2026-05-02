"""Compatibility wrapper for aggregate_ablation_across_backends.

Use `python -m research.agent_eval.aggregate_ablation_across_backends` for new
runs.
"""

from research.agent_eval.aggregate_ablation_across_backends import *  # noqa: F401,F403
from research.agent_eval.aggregate_ablation_across_backends import main


if __name__ == "__main__":
    raise SystemExit(main())
