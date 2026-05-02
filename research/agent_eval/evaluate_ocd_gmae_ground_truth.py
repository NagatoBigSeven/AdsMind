"""Compatibility wrapper for compare_ocd_one_shot_to_reference.

Use `python -m research.agent_eval.compare_ocd_one_shot_to_reference` for new
runs.
"""

from research.agent_eval.compare_ocd_one_shot_to_reference import *  # noqa: F401,F403
from research.agent_eval.compare_ocd_one_shot_to_reference import main


if __name__ == "__main__":
    raise SystemExit(main())
