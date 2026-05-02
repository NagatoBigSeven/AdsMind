"""Compatibility wrapper for rank_one_shot_backend_spread.

Use `python -m research.agent_eval.rank_one_shot_backend_spread` for new runs.
"""

from research.agent_eval.rank_one_shot_backend_spread import *  # noqa: F401,F403
from research.agent_eval.rank_one_shot_backend_spread import main


if __name__ == "__main__":
    raise SystemExit(main())
