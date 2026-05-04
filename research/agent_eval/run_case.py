"""Run a single AdsMind benchmark case and persist structured outputs."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from research.agent_eval.common import (
    CaseRunResult,
    DryRunExecutor,
    build_initial_state_for_case,
    build_result_payload,
    capture_logs,
    copy_session_artifacts,
    current_timestamp,
    get_git_sha,
    load_frozen_config,
    load_manifest_map,
    resolve_repo_path,
    resolve_api_key,
    resolve_runtime_flags,
    write_json,
)
from adsmind.agent.agent import get_agent_executor


def _invoke_with_partial_state(executor: Any, initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute while preserving the last streamed state if a later step crashes."""
    if hasattr(executor, "stream"):
        last_state: Optional[Dict[str, Any]] = None
        try:
            for chunk in executor.stream(
                initial_state,
                config={"recursion_limit": 50},
                stream_mode="values",
            ):
                last_state = chunk
        except Exception as exc:
            if last_state is None:
                raise
            setattr(exc, "_adsmind_partial_state", last_state)
            raise
        return last_state or dict(initial_state)

    return executor.invoke(
        initial_state,
        config={"recursion_limit": 50},
    )


def execute_case(
    *,
    case_row: Dict[str, str],
    frozen_config: Dict[str, Any],
    output_root: Path | str,
    runtime_overrides: Optional[Dict[str, Any]] = None,
    explicit_api_key: Optional[str] = None,
    executor: Optional[Any] = None,
    dry_run: bool = False,
    repo_root: Path | str = ".",
) -> CaseRunResult:
    """Execute one benchmark case and write a self-contained case directory."""
    output_root = resolve_repo_path(output_root, repo_root=repo_root)
    case_dir = output_root / case_row["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    config_path = case_dir / "config.json"
    result_path = case_dir / "result.json"
    log_path = case_dir / "agent_log.txt"

    session_id = f"{case_row['case_id']}-{uuid.uuid4().hex[:8]}"
    api_key, key_source = resolve_api_key(frozen_config, explicit_api_key)
    runtime_flags = resolve_runtime_flags(frozen_config, runtime_overrides)

    config_payload = {
        "git_sha": get_git_sha(repo_root),
        "timestamp": current_timestamp(),
        "api_key_source": key_source,
        "case": case_row,
        "frozen_config": frozen_config,
        "resolved_runtime_flags": runtime_flags,
        "session_id": session_id,
        "dry_run": dry_run,
    }
    write_json(config_path, config_payload)

    initial_state = build_initial_state_for_case(
        case_row=case_row,
        frozen_config=frozen_config,
        session_id=session_id,
        api_key=api_key or "",
        runtime_overrides=runtime_overrides,
        repo_root=repo_root,
    )

    actual_executor = executor or (DryRunExecutor() if dry_run else get_agent_executor())
    final_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start = time.perf_counter()
    with capture_logs(log_path):
        try:
            final_state = _invoke_with_partial_state(actual_executor, initial_state)
        except Exception as exc:  # pragma: no cover - exercised by tests via result schema
            error = str(exc)
            final_state = getattr(exc, "_adsmind_partial_state", final_state)
    wall_clock_sec = time.perf_counter() - start

    artifact_paths = copy_session_artifacts(session_id, case_dir)
    result_payload = build_result_payload(
        case_row=case_row,
        final_state=final_state,
        wall_clock_sec=wall_clock_sec,
        artifact_paths=artifact_paths,
        error=error,
    )
    write_json(result_path, result_payload)
    return CaseRunResult(
        case_dir=case_dir,
        config_path=config_path,
        result_path=result_path,
        log_path=log_path,
        result=result_payload,
    )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run one AdsMind benchmark case.")
    parser.add_argument("--manifest", required=True, help="Path to a dataset manifest CSV")
    parser.add_argument("--config", required=True, help="Path to frozen_config.json")
    parser.add_argument("--case-id", required=True, help="Zero-padded benchmark case id")
    parser.add_argument("--output", required=True, help="Output directory for the case run")
    parser.add_argument("--api-key", default=None, help="Optional explicit API key override")
    parser.add_argument("--dry-run", action="store_true", help="Use a deterministic fake executor")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for running a single case."""
    args = parse_args(argv)
    manifest = load_manifest_map(args.manifest)
    frozen_config = load_frozen_config(args.config)
    case_row = manifest[args.case_id.zfill(2)]
    run = execute_case(
        case_row=case_row,
        frozen_config=frozen_config,
        output_root=args.output,
        explicit_api_key=args.api_key,
        dry_run=args.dry_run,
        repo_root=Path(__file__).resolve().parents[2],
    )
    print(json.dumps(run.result, indent=2, ensure_ascii=False))
    return 0 if run.result["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
