"""Check RUN3 completion for OCD62 overlap12 ablation outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BACKENDS = ("gpt", "claude", "gemini", "grok")
VARIANTS = ("full", "no_slip", "no_forbid", "no_termination", "one_shot")
CASES = tuple(f"{idx:03d}" for idx in range(1, 13))


def summary_path(backend: str) -> Path:
    return (
        ROOT
        / "research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3"
        / backend
        / "all_variants_summary.csv"
    )


def load_status(backend: str) -> dict[tuple[str, str], str]:
    path = summary_path(backend)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            (row.get("case_id", ""), row.get("variant", "")): row.get("success", "")
            for row in csv.DictReader(handle)
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard", default="research/agent_eval/run_configs/ocd62_overlap12_run3/RUN3_DASHBOARD.md")
    args = parser.parse_args(argv)

    lines = [
        "# OCD62 overlap12 RUN3 dashboard",
        "",
        "| case_id | backend | variant | status |",
        "|---|---|---|---|",
    ]
    incomplete = 0
    for backend in BACKENDS:
        status = load_status(backend)
        for case_id in CASES:
            for variant in VARIANTS:
                value = str(status.get((case_id, variant), "")).lower()
                state = "DONE" if value == "true" else "PENDING"
                if state != "DONE":
                    incomplete += 1
                lines.append(f"| {case_id} | {backend} | {variant} | {state} |")

    dashboard = ROOT / args.dashboard
    dashboard.parent.mkdir(parents=True, exist_ok=True)
    dashboard.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(dashboard)
    print(f"incomplete={incomplete}")
    return 0 if incomplete == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
