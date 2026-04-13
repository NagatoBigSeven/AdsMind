"""Sequential batch runner for AdsMind benchmark cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from research.agent_eval.common import (
    load_frozen_config,
    load_manifest,
    normalise_case_ids,
    resolve_repo_path,
    summarize_directory,
    write_summary_csv,
)
from research.agent_eval.run_case import execute_case


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for the batch runner."""
    parser = argparse.ArgumentParser(description="Run AdsMind benchmark cases sequentially.")
    parser.add_argument("--manifest", required=True, help="Path to cmu_manifest.csv")
    parser.add_argument("--config", required=True, help="Path to frozen_config.json")
    parser.add_argument("--output", required=True, help="Output directory for the run")
    parser.add_argument(
        "--case-ids",
        default="",
        help="Optional comma-separated subset of case ids",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip case directories that already contain a valid result.json",
    )
    parser.add_argument("--api-key", default=None, help="Optional explicit API key override")
    parser.add_argument("--dry-run", action="store_true", help="Use the deterministic fake executor")
    return parser.parse_args(argv)


def result_exists(case_dir: Path) -> bool:
    """Treat a case as complete only if result.json exists and is valid JSON."""
    result_path = case_dir / "result.json"
    if not result_path.exists():
        return False
    try:
        with result_path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        return True
    except Exception:
        return False


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for the sequential batch runner."""
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    output_root = resolve_repo_path(args.output, repo_root=repo_root)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_rows = load_manifest(args.manifest)
    if args.case_ids:
        wanted = set(normalise_case_ids(args.case_ids))
        manifest_rows = [row for row in manifest_rows if row["case_id"] in wanted]
    frozen_config = load_frozen_config(args.config)

    failures = []
    total = len(manifest_rows)
    for index, case_row in enumerate(manifest_rows, start=1):
        case_dir = output_root / case_row["case_id"]
        if args.skip_existing and result_exists(case_dir):
            print(f"[{index}/{total}] Skipping case {case_row['case_id']} (existing result.json)")
            continue
        print(
            f"[{index}/{total}] Running case {case_row['case_id']} "
            f"{Path(case_row['slab_file']).name} {case_row['smiles']}"
        )
        try:
            execute_case(
                case_row=case_row,
                frozen_config=frozen_config,
                output_root=output_root,
                explicit_api_key=args.api_key,
                dry_run=args.dry_run,
                repo_root=repo_root,
            )
        except Exception as exc:  # pragma: no cover - batch guardrail
            failures.append({"case_id": case_row["case_id"], "error": str(exc)})

    if failures:
        failure_path = output_root / "batch_failures.json"
        with failure_path.open("w", encoding="utf-8") as handle:
            json.dump(failures, handle, indent=2, ensure_ascii=False)

    summary_rows = summarize_directory(output_root)
    summary_path = write_summary_csv(summary_rows, output_root / "summary.csv")
    print(f"Wrote summary to {summary_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
