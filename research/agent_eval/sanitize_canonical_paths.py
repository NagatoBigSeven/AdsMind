#!/usr/bin/env python3
"""Remove host-specific AdsMind workspace prefixes from canonical result data."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOTS = (
    REPO_ROOT / "research/results/canonical_raw",
    REPO_ROOT / "research/results/adsorbagent_mace_gpt54",
)
TARGET_SUFFIXES = {".json", ".csv"}


@dataclass(frozen=True)
class Replacement:
    label: str
    pattern: bytes | re.Pattern[bytes]

    def count(self, payload: bytes) -> int:
        if isinstance(self.pattern, bytes):
            return payload.count(self.pattern)
        return len(self.pattern.findall(payload))

    def apply(self, payload: bytes) -> bytes:
        if isinstance(self.pattern, bytes):
            return payload.replace(self.pattern, b"")
        return self.pattern.sub(b"", payload)


REPLACEMENTS = (
    Replacement("data_zongmin", b"/data/zongmin/workspace/AdsMind/"),
    Replacement("users_nagato", b"/Users/nagato/workspace/AdsMind/"),
    Replacement(
        "home_workspace",
        re.compile(rb"/home/[A-Za-z0-9._-]+/workspace/AdsMind/"),
    ),
)


def iter_target_files(roots: Iterable[Path] = TARGET_ROOTS) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.name == "agent_log.txt":
                continue
            if path.is_file() and path.suffix in TARGET_SUFFIXES:
                yield path


def sanitize_bytes(payload: bytes) -> tuple[bytes, dict[str, int]]:
    counts = {replacement.label: replacement.count(payload) for replacement in REPLACEMENTS}
    output = payload
    for replacement in REPLACEMENTS:
        output = replacement.apply(output)
    return output, counts


def sanitize_file(path: Path, dry_run: bool) -> tuple[bool, dict[str, int]]:
    original = path.read_bytes()
    sanitized, counts = sanitize_bytes(original)
    changed = sanitized != original
    if changed and not dry_run:
        path.write_bytes(sanitized)
    return changed, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report replacements without writing files.")
    args = parser.parse_args()

    files_scanned = 0
    files_changed = 0
    replacement_counts = {replacement.label: 0 for replacement in REPLACEMENTS}

    for path in iter_target_files():
        files_scanned += 1
        changed, counts = sanitize_file(path, dry_run=args.dry_run)
        if changed:
            files_changed += 1
        for label, count in counts.items():
            replacement_counts[label] += count

    mode = "dry_run" if args.dry_run else "written"
    print(f"mode: {mode}")
    print(f"files_scanned: {files_scanned}")
    print(f"files_changed: {files_changed}")
    for replacement in REPLACEMENTS:
        print(f"{replacement.label}: {replacement_counts[replacement.label]}")
    print(f"total_replacements: {sum(replacement_counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
