"""Summarize an AdsMind run directory into one CSV row per case."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from research.agent_eval.common import summarize_directory, write_summary_csv


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Summarize AdsMind run directories.")
    parser.add_argument("--output", required=True, help="Run directory containing case subdirectories")
    parser.add_argument(
        "--summary-path",
        default="",
        help="Optional explicit path for summary.csv (defaults to <output>/summary.csv)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for summary generation."""
    args = parse_args(argv)
    output_dir = Path(args.output)
    rows = summarize_directory(output_dir)
    summary_path = Path(args.summary_path) if args.summary_path else output_dir / "summary.csv"
    write_summary_csv(rows, summary_path)
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
