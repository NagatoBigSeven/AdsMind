"""Compatibility wrapper for maintenance_merge_split_result_dirs.

Use `python -m research.agent_eval.maintenance_merge_split_result_dirs` for new
maintenance work.
"""

from research.agent_eval.maintenance_merge_split_result_dirs import *  # noqa: F401,F403
from research.agent_eval.maintenance_merge_split_result_dirs import main


if __name__ == "__main__":
    raise SystemExit(main())
