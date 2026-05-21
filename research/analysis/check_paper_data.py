#!/usr/bin/env python3
"""Audit paper-facing AdsMind data files without rewriting them.

The checks here are intentionally conservative: they verify provenance and
surface stale paths or hard-coded values that should be reviewed before a paper
figure/table is regenerated.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import BACKEND_KEYS, backend_result_dir
from research.analysis import build_method_comparison_table as method_tables
from research.analysis import build_ocd62_summary as ocd62_tables


RESULTS = ROOT / "research" / "results"
BASIC = RESULTS / "basic_experiments"
SUMMARIES = BASIC / "summaries"

DATASETS = {
    "cmu20": {"n": 20, "width": 2},
    "ocd62": {"n": 62, "width": 3},
}
VARIANTS = ("full", "no_slip", "no_forbid", "no_termination", "one_shot")
SUMMARY_COMPARE_COLUMNS = (
    "backend_key",
    "backend",
    "llm_model",
    "force_field",
    "calculator_backend",
    "force_field_model",
    "force_field_size",
    "case_id",
    "variant",
    "best_energy",
    "delta_vs_full",
    "iterations",
    "wasted_iterations",
    "waste_ratio",
    "success",
    "slip_count",
    "dissociation_count",
    "tokens_used",
)


@dataclass
class Issue:
    severity: str
    code: str
    message: str


class Auditor:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def error(self, code: str, message: str) -> None:
        self.issues.append(Issue("ERROR", code, message))

    def warn(self, code: str, message: str) -> None:
        self.issues.append(Issue("WARN", code, message))

    def info(self, code: str, message: str) -> None:
        self.issues.append(Issue("INFO", code, message))

    def path(self, path: Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pad_case_id(value: Any, dataset: str) -> str:
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(DATASETS[dataset]["width"])


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def same_number(left: Any, right: Any, tol: float = 1e-7) -> bool:
    lval = parse_float(left)
    rval = parse_float(right)
    if lval is None or rval is None:
        return left in (None, "") and right in (None, "")
    return abs(lval - rval) <= tol


def normalize_bool(value: Any) -> str:
    return str(value).strip().lower()


def result_energy(path: Path) -> float | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    best = parse_float(payload.get("best_energy_eV"))
    if best is not None:
        return best
    last = payload.get("last_analysis") or {}
    if last.get("is_dissociated"):
        return None
    return parse_float(last.get("most_stable_energy_eV"))


def compare_csv_text(generated: pd.DataFrame, path: Path) -> bool:
    buffer = io.StringIO()
    generated.to_csv(buffer, index=False)
    return buffer.getvalue() == path.read_text(encoding="utf-8")


def check_basic_matrix(audit: Auditor) -> None:
    for dataset, spec in DATASETS.items():
        cases = {f"{idx:0{spec['width']}d}" for idx in range(1, spec["n"] + 1)}
        for backend in BACKEND_KEYS:
            backend_dir = BASIC / dataset / "adsmind" / backend_result_dir(backend)
            all_path = backend_dir / "all_variants_summary.csv"
            if not all_path.exists():
                audit.error("missing-all-variants", f"Missing {audit.path(all_path)}")
                continue

            all_rows = read_rows(all_path)
            expected_rows = spec["n"] * len(VARIANTS)
            if len(all_rows) != expected_rows:
                audit.error(
                    "bad-all-variants-row-count",
                    f"{audit.path(all_path)} has {len(all_rows)} rows; expected {expected_rows}",
                )

            all_index: dict[tuple[str, str], dict[str, str]] = {}
            for row in all_rows:
                key = (pad_case_id(row.get("case_id"), dataset), row.get("variant", ""))
                if key in all_index:
                    audit.error(
                        "duplicate-all-variants-row",
                        f"{audit.path(all_path)} duplicates case/variant {key}",
                    )
                all_index[key] = row

            expected_keys = {(case_id, variant) for case_id in cases for variant in VARIANTS}
            missing = sorted(expected_keys - set(all_index))
            extra = sorted(set(all_index) - expected_keys)
            if missing:
                audit.error(
                    "missing-case-variant",
                    f"{audit.path(all_path)} missing {len(missing)} case/variant rows: {missing[:8]}",
                )
            if extra:
                audit.warn(
                    "extra-case-variant",
                    f"{audit.path(all_path)} has {len(extra)} unexpected case/variant rows: {extra[:8]}",
                )

            for variant in VARIANTS:
                variant_path = backend_dir / variant / "summary.csv"
                if not variant_path.exists():
                    audit.error("missing-variant-summary", f"Missing {audit.path(variant_path)}")
                    continue
                variant_rows = read_rows(variant_path)
                if len(variant_rows) != spec["n"]:
                    audit.error(
                        "bad-variant-row-count",
                        f"{audit.path(variant_path)} has {len(variant_rows)} rows; expected {spec['n']}",
                    )

                for row in variant_rows:
                    case_id = pad_case_id(row.get("case_id"), dataset)
                    key = (case_id, variant)
                    all_row = all_index.get(key)
                    if all_row is None:
                        continue
                    for column in SUMMARY_COMPARE_COLUMNS:
                        if column not in row or column not in all_row:
                            continue
                        if row[column] != all_row[column]:
                            audit.error(
                                "variant-all-summary-mismatch",
                                (
                                    f"{dataset}/{backend}/{variant}/{case_id} column {column}: "
                                    f"variant summary={row[column]!r}, all_variants={all_row[column]!r}"
                                ),
                            )

                    run_result = backend_dir / variant / case_id / "result.json"
                    if not run_result.exists():
                        audit.error("missing-result-json", f"Missing {audit.path(run_result)}")
                        continue
                    summary_energy = parse_float(row.get("best_energy"))
                    json_energy = result_energy(run_result)
                    if summary_energy is None and json_energy is None:
                        continue
                    if summary_energy is None or json_energy is None:
                        audit.error(
                            "summary-result-energy-mismatch",
                            (
                                f"{dataset}/{backend}/{variant}/{case_id}: "
                                f"summary best_energy={row.get('best_energy')!r}, result.json={json_energy!r}"
                            ),
                        )
                    elif abs(summary_energy - json_energy) > 1e-6:
                        audit.error(
                            "summary-result-energy-mismatch",
                            (
                                f"{dataset}/{backend}/{variant}/{case_id}: "
                                f"summary best_energy={summary_energy:.12g}, result.json={json_energy:.12g}"
                            ),
                        )


def check_paper_summaries(audit: Auditor) -> None:
    generated_tables = {
        "cmu20_method_comparison.csv": method_tables.build_dataset_table("cmu20"),
        "ocd62_method_comparison.csv": method_tables.build_dataset_table("ocd62"),
        "cmu20_ablation_4backend.csv": method_tables.build_ablation_4backend("cmu20"),
        "ocd62_ablation_4backend.csv": pd.DataFrame(
            ocd62_tables.unified_rows(),
            columns=[
                "case_id",
                "ocd_id",
                "surface_formula",
                "adsorbate",
                "backend_key",
                "backend",
                "llm_model",
                "force_field",
                "calculator_backend",
                "force_field_model",
                "force_field_size",
                "variant",
                "best_energy_eV",
                "success",
                "run_path",
                "iterations",
                "wasted_iterations",
                "waste_ratio",
                "slip_count",
                "dissociation_count",
                "tokens_used",
            ],
        ),
    }

    for filename, generated in generated_tables.items():
        path = SUMMARIES / filename
        if not path.exists():
            audit.error("missing-paper-summary", f"Missing {audit.path(path)}")
            continue
        if compare_csv_text(generated, path):
            audit.info("paper-summary-current", f"{audit.path(path)} matches raw summaries")
        else:
            audit.error(
                "stale-paper-summary",
                f"{audit.path(path)} does not match data rebuilt in memory from raw summaries",
            )


def check_processed_plot_inputs(audit: Auditor) -> None:
    expected = [
        RESULTS / "processed" / "figure3" / "iteration_convergence.csv",
        RESULTS / "processed" / "figure3" / "ablation_4backend.csv",
        RESULTS / "processed" / "si_figures" / "basic_experiments" / "cmu20" / "gpt" / "full" / "summary.csv",
        RESULTS
        / "processed"
        / "si_figures"
        / "advanced_experiments"
        / "chemical_slip_interpretability"
        / "cmu20"
        / "slip_analysis.csv",
        RESULTS
        / "processed"
        / "si_figures"
        / "advanced_experiments"
        / "mace_force_field_sensitivity"
        / "cmu20_gpt_full_mace_mp0_large"
        / "ablation_summary.csv",
    ]
    for path in expected:
        if not path.exists():
            audit.warn(
                "missing-processed-plot-input",
                f"Plot notebook input is absent until prep scripts are rerun: {audit.path(path)}",
            )

    figure3_script = (
        ROOT / "research" / "paper_plots" / "scripts" / "prepare_figure3_data.py"
    ).read_text(encoding="utf-8")
    si_script = (
        ROOT / "research" / "paper_plots" / "scripts" / "prepare_si_data.py"
    ).read_text(encoding="utf-8")
    if "'basic_experiments', 'cmu20', 'summaries', 'method_comparison.csv'" in figure3_script:
        audit.warn(
            "stale-prep-script-path",
            "prepare_figure3_data.py still points to the removed cmu20/summaries folder",
        )
    if "'basic_experiments', 'cmu20',\n                               long_be, var" in si_script:
        audit.warn(
            "stale-prep-script-path",
            "prepare_si_data.py still omits the adsmind/ component for backend summaries",
        )
    if r"adsorb-agent\adsorb-agent" in si_script:
        audit.warn(
            "stale-prep-script-path",
            "prepare_si_data.py still uses a Windows backslash in the Adsorb-Agent baseline path",
        )

    convergence = (
        RESULTS
        / "advanced_experiments"
        / "case_studies"
        / "iteration_convergence"
        / "cmu20"
        / "all_backends"
        / "full"
        / "iteration_convergence.csv"
    )
    if convergence.exists():
        summary_cache: dict[str, dict[str, str]] = {}
        mismatches: list[str] = []
        for row in read_rows(convergence):
            backend = row.get("backend", "")
            case_id = pad_case_id(row.get("case_id", ""), "cmu20")
            if backend not in summary_cache:
                summary_path = (
                    BASIC / "cmu20" / "adsmind" / backend / "full" / "summary.csv"
                )
                if not summary_path.exists():
                    continue
                summary_cache[backend] = {
                    pad_case_id(item["case_id"], "cmu20"): item.get("best_energy", "")
                    for item in read_rows(summary_path)
                }
            expected = summary_cache[backend].get(case_id, "")
            actual = row.get("final_best", "")
            if not same_number(actual, expected, tol=1e-6):
                mismatches.append(f"{backend}/case {case_id}: {actual} != {expected}")
        if mismatches:
            audit.error(
                "iteration-convergence-final-best-mismatch",
                "iteration_convergence.csv final_best does not match valid Full summary "
                f"energies; first mismatches: {'; '.join(mismatches[:5])}",
            )


def extract_hardcoded_figure5_values() -> list[float] | None:
    path = ROOT / "research" / "paper_plots" / "figure5" / "figure5_vasp_validation.ipynb"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    for cell in payload.get("cells", []):
        source = "".join(cell.get("source", []))
        match = re.search(r"adsmind\s*=\s*\[(.*?)\]", source, re.S)
        if match:
            return [float(value) for value in re.findall(r"[-+]?\d+\.\d+", match.group(1))]
    return None


def extract_si_dft_values() -> list[float] | None:
    path = ROOT / "overleaf" / "si.tex"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    block_match = re.search(
        r"\\label\{tab:si-dft-systems\}(.*?)(?:\\bottomrule|\\end\{tabular\})",
        text,
        re.S,
    )
    if not block_match:
        return None
    rows = {}
    for line in block_match.group(1).splitlines():
        match = re.match(r"\s*(\d{2})\s*&.*?&\s*\$?([-+]?\d+\.\d+)\$?\s*\\\\", line)
        if match:
            rows[match.group(1)] = float(match.group(2))
    dft_cases = ("01", "02", "03", "04", "09", "10")
    if not all(case_id in rows for case_id in dft_cases):
        return None
    return [rows[case_id] for case_id in dft_cases]


def check_dft_values(audit: Auditor) -> None:
    dft_cases = ("01", "02", "03", "04", "09", "10")
    expected = []
    for case_id in dft_cases:
        path = (
            BASIC
            / "cmu20"
            / "adsmind"
            / backend_result_dir("gpt")
            / "full"
            / "summary.csv"
        )
        rows = {pad_case_id(row["case_id"], "cmu20"): row for row in read_rows(path)}
        expected.append(float(rows[case_id]["best_energy"]))

    figure_values = extract_hardcoded_figure5_values()
    if figure_values is None:
        audit.warn("missing-figure5-adsmind-values", "Could not find hard-coded AdsMind values in Figure 5 notebook")
    si_values = extract_si_dft_values()
    if si_values is None:
        audit.warn("missing-si-dft-adsmind-values", "Could not find AdsMind values in SI DFT table")

    for label, values in (("Figure 5 notebook", figure_values), ("SI DFT table", si_values)):
        if values is None:
            continue
        mismatches = []
        for case_id, paper_value, raw_value in zip(dft_cases, values, expected):
            if abs(paper_value - raw_value) > 5e-3:
                mismatches.append((case_id, paper_value, raw_value))
        if mismatches:
            formatted = ", ".join(
                f"{case}: paper={paper:.3f}, gpt_full_raw={raw:.3f}"
                for case, paper, raw in mismatches
            )
            audit.warn(
                "figure5-caption-data-mismatch",
                (
                    f"{label} says AdsMind is GPT-5.4 Full, "
                    f"but values differ from GPT-5.4 Full for: {formatted}"
                ),
            )
    results_tex = ROOT / "overleaf" / "sections" / "3_Results.tex"
    if results_tex.exists() and "regenerate images/figure5_vasp_validation.png" in results_tex.read_text(encoding="utf-8"):
        audit.warn(
            "figure5-image-needs-regeneration",
            "Figure 5 text/table/notebook now use GPT-5.4 Full values, but the included PNG is marked for Yuyang to regenerate.",
        )


def check_manuscript_policy_flags(audit: Auditor) -> None:
    files = [
        ROOT / "overleaf" / "sections" / "2_Method.tex",
        ROOT / "overleaf" / "sections" / "3_Results.tex",
        ROOT / "overleaf" / "sections" / "4_DiscussionConclusion.tex",
        ROOT / "overleaf" / "si.tex",
    ]
    patterns = {
        "random-baseline-still-present": re.compile(r"\b[Rr]andom\b"),
        "statistics-still-present": re.compile(
            r"\b(statistical|statistics|p-value|p value|t-test|ANOVA|Pearson|Spearman)\b",
            re.I,
        ),
        "efficiency-claim-still-present": re.compile(
            r"\b(efficien\w*|token\w*|cost|costs|costly|low-cost|computational cost|cost--accuracy)\b",
            re.I,
        ),
    }
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for code, pattern in patterns.items():
            hits = pattern.findall(text)
            if hits:
                audit.warn(
                    code,
                    f"{audit.path(path)} still contains {len(hits)} occurrence(s) relevant to meeting cleanup",
                )


def check_model_period(audit: Auditor) -> None:
    models = set()
    for backend in BACKEND_KEYS:
        path = BASIC / "cmu20" / "adsmind" / backend_result_dir(backend) / "full" / "summary.csv"
        if not path.exists():
            continue
        rows = read_rows(path)
        models.update(row.get("llm_model", "") for row in rows if row.get("llm_model"))
    audit.info("llm-models-present", f"Current CMU20 backend models: {', '.join(sorted(models))}")
    if any("gemini-2.5" in model for model in models):
        audit.warn(
            "model-period-mixed",
            (
                "Gemini data are still Gemini 2.5 Pro while GPT/Claude/Grok use "
                "newer-generation labels; rerun Gemini-3.1-Pro-Preview with the same "
                "frozen remote configuration and replace the Gemini 2.5 Pro summaries."
            ),
        )


def print_report(audit: Auditor) -> None:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    issues = sorted(audit.issues, key=lambda issue: (order[issue.severity], issue.code, issue.message))
    counts = {severity: sum(issue.severity == severity for issue in issues) for severity in order}
    print("# Paper data audit")
    print()
    print(f"Errors: {counts['ERROR']}  Warnings: {counts['WARN']}  Info: {counts['INFO']}")
    print()
    for issue in issues:
        print(f"[{issue.severity}] {issue.code}: {issue.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a non-zero exit")
    args = parser.parse_args()

    audit = Auditor()
    check_basic_matrix(audit)
    check_paper_summaries(audit)
    check_processed_plot_inputs(audit)
    check_dft_values(audit)
    check_manuscript_policy_flags(audit)
    check_model_period(audit)
    print_report(audit)

    has_errors = any(issue.severity == "ERROR" for issue in audit.issues)
    has_warnings = any(issue.severity == "WARN" for issue in audit.issues)
    if has_errors or (args.strict and has_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
