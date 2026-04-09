"""Environment preflight checks for AdsMind."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any

from src.calculators import get_available_backends
from src.llms import get_available_llm_backends
from src.utils.config import get_calculator_backend, get_llm_backend_name


def gather_preflight_report() -> dict[str, Any]:
    """Collect a lightweight environment report for the current installation."""
    from src.agent.agent import get_agent_executor

    report: dict[str, Any] = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "configured_llm_backend": get_llm_backend_name(),
        "configured_calculator_backend": get_calculator_backend(),
        "available_llm_backends": [],
        "available_calculator_backends": [],
        "agent_graph_compiles": False,
    }

    report["available_llm_backends"] = get_available_llm_backends()
    report["available_calculator_backends"] = get_available_backends()
    get_agent_executor()
    report["agent_graph_compiles"] = True
    return report


def run_preflight(strict: bool = False) -> tuple[int, dict[str, Any]]:
    """Run preflight checks and return a process-style status code plus report."""
    try:
        report = gather_preflight_report()
    except Exception as exc:
        return 1, {"status": "error", "message": str(exc)}

    if strict:
        if not report["agent_graph_compiles"]:
            return 1, report
        if not report["available_llm_backends"]:
            return 1, report
        if not report["available_calculator_backends"]:
            return 1, report

    return 0, report


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for environment preflight."""
    parser = argparse.ArgumentParser(description="Run AdsMind environment preflight checks.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the preflight report as JSON.",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Enable strict mode suitable for CI quality gates.",
    )
    args = parser.parse_args(argv)

    code, report = run_preflight(strict=args.ci)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("AdsMind preflight")
        print(f"Python: {report.get('python_version', 'unknown')}")
        print(f"Platform: {report.get('platform', 'unknown')}")
        print(f"Configured LLM backend: {report.get('configured_llm_backend', 'unknown')}")
        print(
            "Available LLM backends: "
            + ", ".join(report.get("available_llm_backends", []))
        )
        print(
            "Available calculator backends: "
            + ", ".join(report.get("available_calculator_backends", []))
        )
        print(
            "Agent graph compiles: "
            + ("yes" if report.get("agent_graph_compiles") else "no")
        )
        if report.get("status") == "error":
            print(f"Error: {report.get('message')}")

    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
