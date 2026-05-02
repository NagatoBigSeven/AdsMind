"""Compatibility wrapper for legacy_package_results.

This packaging workflow predates the canonical_raw result layout. Prefer the
documented canonical result sources for new manuscript analysis.
"""

from research.agent_eval.legacy_package_results import *  # noqa: F401,F403
from research.agent_eval.legacy_package_results import main


if __name__ == "__main__":
    raise SystemExit(main())
