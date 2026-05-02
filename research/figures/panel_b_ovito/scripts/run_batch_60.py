"""Batch-render all 60 selected Panel B cases via OVITO Tachyon (jmol palette)."""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(os.environ.get("ADSMIND_REPO_ROOT", Path(__file__).resolve().parents[4])).resolve()
MANIFEST = Path(
    os.environ.get(
        "PANEL_B_MANIFEST",
        REPO / "research/results/analysis/panel_b_assets_20260429/manifest.csv",
    )
)
PYTHON = Path(
    os.environ.get(
        "ADSMIND_OVITO_PYTHON",
        str(REPO / ".venv-ovito/bin/python")
        if (REPO / ".venv-ovito/bin/python").exists()
        else (shutil.which("python") or sys.executable),
    )
)
RENDER_SCRIPT = REPO / "research/figures/panel_b_ovito/scripts/catalyst_surface_visualizer.py"
OUT_DIR = REPO / "research/figures/panel_b_ovito/renders/batch_60"


def load_cases():
    if not MANIFEST.exists():
        raise FileNotFoundError(
            f"Panel B manifest not found: {MANIFEST}. Set PANEL_B_MANIFEST to the curated CSV."
        )
    cases = []
    seen = set()
    with MANIFEST.open() as f:
        for row in csv.DictReader(f):
            if row["selected_for_panel_b"].lower() != "true":
                continue
            bucket = row["selection_bucket"]
            out = OUT_DIR / bucket / Path(row["png_path"]).name
            key = str(out)
            if key in seen:
                continue
            seen.add(key)
            cases.append({
                "bucket": bucket,
                "xyz": REPO / row["source_xyz"],
                "out": out,
                "id": f"{bucket}/{row['case_id']}",
            })
    return cases


def main() -> int:
    cases = load_cases()
    print(f"ovito batch: {len(cases)} cases → {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    fails = 0
    for i, c in enumerate(cases, 1):
        if c["out"].exists():
            print(f"[{i}/{len(cases)}] SKIP {c['id']}")
            continue
        c["out"].parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(PYTHON), str(RENDER_SCRIPT), str(c["xyz"]),
            "-o", str(c["out"]),
            "--renderer", "tachyon",
            "--quality", "high",
            "--no-expand",
        ]
        t1 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        dt = time.time() - t1
        if r.returncode != 0 or not c["out"].exists():
            fails += 1
            reason = f"code {r.returncode}" if r.returncode != 0 else "PNG missing"
            print(f"[{i}/{len(cases)}] FAIL {c['id']} ({reason}, {dt:.0f}s)")
            tail = (r.stderr or r.stdout or "")[-1200:]
            print(tail)
            continue
        sz = c["out"].stat().st_size // 1024
        print(f"[{i}/{len(cases)}] OK   {c['id']} ({dt:.0f}s, {sz}KB)")
    print(f"\novito batch done in {time.time()-t0:.0f}s, fails={fails}")
    return 0 if fails == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
