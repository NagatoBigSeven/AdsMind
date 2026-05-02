"""Compatibility wrapper for compare_two_backend_ablation.

Use `python -m research.agent_eval.compare_two_backend_ablation` for new runs.
"""

from research.agent_eval.compare_two_backend_ablation import *  # noqa: F401,F403
from research.agent_eval.compare_two_backend_ablation import main


if __name__ == "__main__":
    raise SystemExit(main())
