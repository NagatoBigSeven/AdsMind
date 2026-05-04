"""Build CMU20 and OCD62 cost-vs-depth method comparison tables."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "research" / "results" / "canonical_raw"
BASIC_DIR = ROOT / "research" / "results" / "basic_tests"
OCD62_MANIFEST = ROOT / "datasets" / "ocd62" / "ocd62_manifest.csv"

BACKENDS = ["gemini", "grok4", "openai_gpt54", "anthropic_sonnet46"]

DATASETS = {
    "cmu20": {
        "n_cases": 20,
        "case_width": 2,
        "random_dir": "cmu20/random_baseline_n20",
        "heuristic_dir": "cmu20/heuristic_baseline",
    },
    "ocd62": {
        "n_cases": 62,
        "case_width": 3,
        "random_dir": "ocd62/random_baseline_n20",
        "heuristic_dir": "ocd62/heuristic_baseline",
    },
}


def ablation_dir(dataset: str, backend: str) -> Path:
    if dataset in {"cmu20", "ocd62"}:
        return CANONICAL / dataset / f"{backend}_ablation"
    return CANONICAL / f"{dataset}_{backend}_ablation"


def case_ids(dataset: str) -> list[str]:
    width = DATASETS[dataset]["case_width"]
    return [f"{i:0{width}d}" for i in range(1, DATASETS[dataset]["n_cases"] + 1)]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"case_id": str}, keep_default_na=True)


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def to_success(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "success", "1", "yes"})


def pad_case_id(value: object, dataset: str) -> str:
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(DATASETS[dataset]["case_width"])


def result_json_path(dataset: str, backend: str, variant: str, case_id: str) -> Path:
    return ablation_dir(dataset, backend) / variant / case_id / "result.json"


def load_ocd62_manifest() -> pd.DataFrame:
    return pd.read_csv(OCD62_MANIFEST, dtype=str)


def adsorbate_label(meta: pd.Series) -> str:
    for key in ("adsorbate", "adsorbate_name", "smiles"):
        if key in meta and pd.notna(meta[key]):
            return str(meta[key])
    return ""


def parse_cmu_surface_from_slab(slab_file: str) -> str:
    stem = Path(slab_file).stem
    pieces = stem.split("_")
    if len(pieces) >= 2 and pieces[0].isdigit():
        return pieces[1]
    return stem


def load_metadata(dataset: str, case_id: str) -> dict[str, object]:
    if dataset == "ocd62":
        manifest = load_ocd62_manifest().set_index("case_id")
        meta = manifest.loc[case_id]
        return {
            "benchmark_id": meta.get("ocd_id", ""),
            "case_id": case_id,
            "surface": meta["surface_formula"],
            "adsorbate": adsorbate_label(meta),
        }

    path = result_json_path(dataset, "gemini", "full", case_id)
    if not path.exists():
        return {"benchmark_id": case_id, "case_id": case_id}
    with path.open(encoding="utf-8") as handle:
        result = json.load(handle)
    metadata = result.get("case_metadata") or {}

    surface = metadata.get("surface_formula") or parse_cmu_surface_from_slab(str(metadata.get("slab_file", "")))
    adsorbate = metadata.get("adsorbate_name") or metadata.get("smiles")

    return {
        "benchmark_id": case_id,
        "case_id": case_id,
        "surface": surface,
        "adsorbate": adsorbate,
    }


def load_adsmind_backend_rows(dataset: str, backend: str, variant: str) -> pd.DataFrame:
    path = ablation_dir(dataset, backend) / "ablation_summary.csv"
    df = read_csv(path)
    subset = df[df["variant"] == variant].copy()
    out = pd.DataFrame(
        {
            "case_id": subset["case_id"].map(lambda value: pad_case_id(value, dataset)),
            "energy": to_num(subset["best_energy"]),
            "relax": to_num(subset["iterations"]),
            "success": to_success(subset["success"]),
        }
    )
    out.loc[~out["success"], "energy"] = np.nan
    return out


def add_adsmind_columns(table: pd.DataFrame, dataset: str, variant: str, prefix: str) -> None:
    for backend in BACKENDS:
        rows = load_adsmind_backend_rows(dataset, backend, variant).set_index("case_id")
        for metric in ["energy", "relax", "success"]:
            table[f"{prefix}_{backend}_{metric}"] = table["case_id"].map(rows[metric])

    energy_cols = [f"{prefix}_{backend}_energy" for backend in BACKENDS]
    relax_cols = [f"{prefix}_{backend}_relax" for backend in BACKENDS]
    success_cols = [f"{prefix}_{backend}_success" for backend in BACKENDS]

    table[f"{prefix}_energy_best4"] = table[energy_cols].min(axis=1, skipna=True)
    table[f"{prefix}_energy_mean4"] = table[energy_cols].mean(axis=1, skipna=True)
    table[f"{prefix}_best4"] = table[f"{prefix}_energy_best4"]
    table[f"{prefix}_mean4"] = table[f"{prefix}_energy_mean4"]
    table[f"{prefix}_energy"] = table[f"{prefix}_energy_mean4"]
    table[f"{prefix}_relax"] = table[relax_cols].mean(axis=1, skipna=True)
    table[f"{prefix}_success"] = table[success_cols].mean(axis=1, skipna=True)
    table[f"{prefix}_success_any4"] = table[success_cols].any(axis=1)
    table[f"{prefix}_success_all4"] = table[success_cols].all(axis=1)


def add_random_columns(table: pd.DataFrame, dataset: str) -> None:
    path = CANONICAL / DATASETS[dataset]["random_dir"] / "summary.csv"
    df = read_csv(path)
    df["case_id"] = df["case_id"].map(lambda value: pad_case_id(value, dataset))
    df["energy"] = to_num(df["best_energy"])
    df["success"] = to_success(df["status"]) & df["energy"].notna()
    df.loc[~df["success"], "energy"] = np.nan
    rows = df.set_index("case_id")

    table["random_n20_energy"] = table["case_id"].map(rows["energy"])
    table["random_n20_relax"] = 20.0
    table["random_n20_success"] = table["case_id"].map(rows["success"]).astype(float)


def add_heuristic_columns(table: pd.DataFrame, dataset: str) -> None:
    path = CANONICAL / DATASETS[dataset]["heuristic_dir"] / "summary.csv"
    df = read_csv(path)
    df["case_id"] = df["case_id"].map(lambda value: pad_case_id(value, dataset))
    df["energy"] = to_num(df["best_energy"])
    df["relax"] = to_num(df["n_sites"])
    df["success"] = to_success(df["status"]) & df["energy"].notna()
    df.loc[~df["success"], "energy"] = np.nan
    rows = df.set_index("case_id")

    table["heuristic_energy"] = table["case_id"].map(rows["energy"])
    table["heuristic_relax"] = table["case_id"].map(rows["relax"])
    table["heuristic_success"] = table["case_id"].map(rows["success"]).astype(float)


def add_adsorbagent_columns(table: pd.DataFrame, dataset: str) -> None:
    table["adsorbagent_energy"] = np.nan
    table["adsorbagent_relax"] = np.nan
    table["adsorbagent_success"] = np.nan

    if dataset != "cmu20":
        return

    path = ROOT / "research" / "results" / "adsorbagent_mace_gpt54" / "adsorbagent_mace_summary.csv"
    df = read_csv(path)
    df["case_id"] = df["case_id"].map(lambda value: pad_case_id(value, dataset))
    df["energy"] = to_num(df["best_adsorption_energy_eV"])
    df["relax"] = to_num(df["adsorbagent_configs_tested"])
    df["success"] = to_success(df["status"]) & (to_num(df["valid_traj_count"]) > 0) & df["energy"].notna()
    df.loc[~df["success"], ["energy", "relax"]] = np.nan
    rows = df.set_index("case_id")

    table["adsorbagent_energy"] = table["case_id"].map(rows["energy"])
    table["adsorbagent_relax"] = table["case_id"].map(rows["relax"])
    table["adsorbagent_success"] = table["case_id"].map(rows["success"]).astype(float)


def build_dataset_table(dataset: str) -> pd.DataFrame:
    rows = [load_metadata(dataset, case_id) for case_id in case_ids(dataset)]
    table = pd.DataFrame(rows)

    add_adsmind_columns(table, dataset, "single_shot", "adsmind_1shot")
    add_adsmind_columns(table, dataset, "full", "adsmind_full")
    add_random_columns(table, dataset)
    add_heuristic_columns(table, dataset)
    add_adsorbagent_columns(table, dataset)

    first_cols = [
        "benchmark_id",
        "case_id",
        "surface",
        "adsorbate",
        "adsmind_1shot_energy",
        "adsmind_1shot_energy_best4",
        "adsmind_1shot_energy_mean4",
        "adsmind_1shot_best4",
        "adsmind_1shot_mean4",
        "adsmind_1shot_relax",
        "adsmind_1shot_success",
        "adsmind_full_energy",
        "adsmind_full_energy_best4",
        "adsmind_full_energy_mean4",
        "adsmind_full_best4",
        "adsmind_full_mean4",
        "adsmind_full_relax",
        "adsmind_full_success",
        "random_n20_energy",
        "random_n20_relax",
        "random_n20_success",
        "heuristic_energy",
        "heuristic_relax",
        "heuristic_success",
        "adsorbagent_energy",
        "adsorbagent_relax",
        "adsorbagent_success",
    ]
    remaining = [col for col in table.columns if col not in first_cols]
    return table[[col for col in first_cols if col in table.columns] + remaining]


METHODS = [
    ("AdsMind_1shot", "adsmind_1shot"),
    ("AdsMind_full", "adsmind_full"),
    ("Random_n20", "random_n20"),
    ("Heuristic", "heuristic"),
    ("AdsorbAgent", "adsorbagent"),
]


def method_long_frame(table: pd.DataFrame, dataset: str) -> pd.DataFrame:
    frames = []
    for method, prefix in METHODS:
        if dataset != "cmu20" and method == "AdsorbAgent":
            continue
        frames.append(
            pd.DataFrame(
                {
                    "method": method,
                    "dataset": dataset,
                    "case_id": table["case_id"],
                    "relax": table[f"{prefix}_relax"],
                    "energy_eV": table[f"{prefix}_energy"],
                    "success": table[f"{prefix}_success"],
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def summarize_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    long = pd.concat([method_long_frame(table, dataset) for dataset, table in tables.items()], ignore_index=True)
    grouped = long.groupby(["method", "dataset"], sort=False)
    summary = grouped.agg(
        n_cases=("case_id", "nunique"),
        mean_relax=("relax", "mean"),
        mean_energy_eV=("energy_eV", "mean"),
        median_energy_eV=("energy_eV", "median"),
        std_energy_eV=("energy_eV", "std"),
        success_rate=("success", "mean"),
    ).reset_index()

    success_conditioned = (
        long[long["success"] > 0]
        .groupby(["method", "dataset"], sort=False)["energy_eV"]
        .mean()
        .rename("mean_energy_eV_among_success")
        .reset_index()
    )
    summary = summary.merge(success_conditioned, on=["method", "dataset"], how="left")

    order = {
        (method, dataset): i
        for i, (dataset, method) in enumerate(
            (dataset, method)
            for dataset in tables
            for method, _ in METHODS
            if not (dataset != "cmu20" and method == "AdsorbAgent")
        )
    }
    summary["_order"] = summary.apply(lambda row: order[(row["method"], row["dataset"])], axis=1)
    return summary.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def method_category(method: str) -> str:
    return {
        "AdsMind_1shot": "open-loop",
        "AdsMind_full": "iterative",
        "Random_n20": "brute-force",
        "Heuristic": "brute-force",
        "AdsorbAgent": "brute-force",
    }[method]


def display_dataset(dataset: str) -> str:
    return {"cmu20": "CMU20", "ocd62": "OCD62"}[dataset]


def display_method(method: str) -> str:
    return {
        "AdsMind_1shot": "AdsMind 1-Shot",
        "AdsMind_full": "AdsMind Full",
        "Random_n20": "Random N=20",
        "Heuristic": "Heuristic",
        "AdsorbAgent": "Adsorb-Agent",
    }[method]


def fmt_float(value: float, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.{digits}f}"


def fmt_percent(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value * 100:.1f}%"


def write_publication_tables(summary: pd.DataFrame) -> None:
    rows = []
    for _, row in summary.iterrows():
        rows.append(
            {
                "Dataset": display_dataset(row["dataset"]),
                "Method": display_method(row["method"]),
                "Class": method_category(row["method"]),
                "n": int(row["n_cases"]),
                "Relax/case": fmt_float(row["mean_relax"], 2),
                "Success": fmt_percent(row["success_rate"]),
                "Mean E (eV)": fmt_float(row["mean_energy_eV"], 3),
                "Median E (eV)": fmt_float(row["median_energy_eV"], 3),
            }
        )

    md_lines = [
        "# Brute-force vs iterative search table",
        "",
        "Raw adsorption energies are reported in eV; more negative values indicate deeper configurations.",
        "",
        "| Dataset | Method | Class | n | Relax/case | Success | Mean E (eV) | Median E (eV) |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['Dataset']} | {row['Method']} | {row['Class']} | {row['n']} | "
            f"{row['Relax/case']} | {row['Success']} | {row['Mean E (eV)']} | {row['Median E (eV)']} |"
        )
    md_lines.append("")
    (BASIC_DIR / "method_comparison_table.md").write_text("\n".join(md_lines), encoding="utf-8")

    tex_lines = [
        "% Draft table for human merge. Generated by research/analysis/build_method_comparison_table.py.",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Search-strategy comparison under matched MACE-MP-0 small physics. Raw adsorption energies are reported in eV; more negative values indicate deeper configurations.}",
        "\\label{tab:method-comparison}",
        "\\begin{tabular}{lllrrrrr}",
        "\\toprule",
        "Dataset & Method & Class & $n$ & Relax/case & Success (\\%) & Mean $E$ & Median $E$ \\\\",
        "\\midrule",
    ]
    for row in rows:
        success = row["Success"].replace("%", "")
        tex_lines.append(
            f"{row['Dataset']} & {row['Method']} & {row['Class']} & {row['n']} & "
            f"{row['Relax/case']} & {success} & {row['Mean E (eV)']} & {row['Median E (eV)']} \\\\"
        )
    tex_lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (BASIC_DIR / "method_comparison_table.tex").write_text("\n".join(tex_lines), encoding="utf-8")


def summarize_basic_tests(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset, table in tables.items():
        full_success_cols = [f"adsmind_full_{backend}_success" for backend in BACKENDS]
        shot_success_cols = [f"adsmind_1shot_{backend}_success" for backend in BACKENDS]
        full_energy_cols = [f"adsmind_full_{backend}_energy" for backend in BACKENDS]
        shot_energy_cols = [f"adsmind_1shot_{backend}_energy" for backend in BACKENDS]

        full_success_values = table[full_success_cols].to_numpy(dtype=float).ravel()
        shot_success_values = table[shot_success_cols].to_numpy(dtype=float).ravel()
        full_energies = table[full_energy_cols].apply(pd.to_numeric, errors="coerce")
        shot_energies = table[shot_energy_cols].apply(pd.to_numeric, errors="coerce")

        deltas = []
        for full_col, shot_col in zip(full_energy_cols, shot_energy_cols):
            paired = table[[full_col, shot_col]].apply(pd.to_numeric, errors="coerce").dropna()
            deltas.extend((paired[shot_col] - paired[full_col]).tolist())

        full_ranges = full_energies.max(axis=1, skipna=True) - full_energies.min(axis=1, skipna=True)
        shot_ranges = shot_energies.max(axis=1, skipna=True) - shot_energies.min(axis=1, skipna=True)
        full_ranges = full_ranges[full_energies.notna().sum(axis=1) >= 2]
        shot_ranges = shot_ranges[shot_energies.notna().sum(axis=1) >= 2]

        rows.append(
            {
                "dataset": dataset,
                "n_cases": len(table),
                "full_success_runs": int(np.nansum(full_success_values)),
                "full_total_runs": int(np.isfinite(full_success_values).sum()),
                "full_success_rate": float(np.nanmean(full_success_values)),
                "one_shot_success_runs": int(np.nansum(shot_success_values)),
                "one_shot_total_runs": int(np.isfinite(shot_success_values).sum()),
                "one_shot_success_rate": float(np.nanmean(shot_success_values)),
                "paired_full_vs_1shot_successes": len(deltas),
                "mean_delta_1shot_minus_full_eV": float(np.mean(deltas)) if deltas else np.nan,
                "median_delta_1shot_minus_full_eV": float(np.median(deltas)) if deltas else np.nan,
                "full_mean_4backend_range_eV": float(full_ranges.mean()) if len(full_ranges) else np.nan,
                "one_shot_mean_4backend_range_eV": float(shot_ranges.mean()) if len(shot_ranges) else np.nan,
                "random_n20_mean_relax": float(table["random_n20_relax"].mean()),
                "heuristic_mean_relax": float(table["heuristic_relax"].mean()),
            }
        )
    return pd.DataFrame(rows)


def write_basic_test_report(basic: pd.DataFrame) -> None:
    BASIC_DIR.mkdir(parents=True, exist_ok=True)
    basic.to_csv(BASIC_DIR / "full_vs_1shot_summary.csv", index=False)
    lines = [
        "# Basic Test Summary",
        "",
        "This table covers Full vs 1-Shot reliability, success-conditioned energy deltas, cross-backend range, and random/heuristic cost baselines.",
        "",
        "Delta is defined as `E_1shot - E_full` on paired successful backend-case runs; positive values mean AdsMind Full reached a lower-energy configuration.",
        "",
        "| Dataset | n cases | Full success | 1-Shot success | Paired successes | Mean delta (eV) | Median delta (eV) | Full backend range (eV) | 1-Shot backend range (eV) | Random cost | Heuristic cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in basic.iterrows():
        lines.append(
            f"| {display_dataset(row['dataset'])} | {int(row['n_cases'])} | "
            f"{int(row['full_success_runs'])}/{int(row['full_total_runs'])} ({fmt_percent(row['full_success_rate'])}) | "
            f"{int(row['one_shot_success_runs'])}/{int(row['one_shot_total_runs'])} ({fmt_percent(row['one_shot_success_rate'])}) | "
            f"{int(row['paired_full_vs_1shot_successes'])} | "
            f"{fmt_float(row['mean_delta_1shot_minus_full_eV'], 3)} | "
            f"{fmt_float(row['median_delta_1shot_minus_full_eV'], 3)} | "
            f"{fmt_float(row['full_mean_4backend_range_eV'], 3)} | "
            f"{fmt_float(row['one_shot_mean_4backend_range_eV'], 3)} | "
            f"{fmt_float(row['random_n20_mean_relax'], 2)} | "
            f"{fmt_float(row['heuristic_mean_relax'], 2)} |"
        )
    lines.append("")
    (BASIC_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Basic Tests",
                "",
                "Paper-facing basic-test outputs. The benchmark names used here are `CMU20` and `OCD62`.",
                "",
                "Files:",
                "",
                "- `full_vs_1shot_summary.csv`: Full vs 1-Shot reliability, energy deltas, backend ranges, and random/heuristic cost summaries.",
                "- `method_comparison_summary.csv`: Brute-force/open-loop/iterative method comparison for CMU20 and OCD62.",
                "- `method_comparison_table.md` and `method_comparison_table.tex`: human-facing drafts of the same method comparison.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def validate_outputs(tables: dict[str, pd.DataFrame], summary: pd.DataFrame) -> None:
    for dataset, expected in {"cmu20": 20, "ocd62": 62}.items():
        observed = len(tables[dataset])
        if observed != expected:
            raise ValueError(f"{dataset}: expected {expected} rows, observed {observed}")
    if len(summary) != 9:
        raise ValueError(f"Expected 9 main summary rows, observed {len(summary)}")


def main() -> None:
    BASIC_DIR.mkdir(parents=True, exist_ok=True)

    tables = {dataset: build_dataset_table(dataset) for dataset in DATASETS}
    for dataset, table in tables.items():
        public_path = BASIC_DIR / f"{display_dataset(dataset).lower()}_method_comparison.csv"
        table.to_csv(public_path, index=False)
        print(f"Wrote {public_path.relative_to(ROOT)} ({len(table)} rows)")

    summary = summarize_tables(tables)
    summary.to_csv(BASIC_DIR / "method_comparison_summary.csv", index=False)
    write_publication_tables(summary)
    write_basic_test_report(summarize_basic_tests(tables))
    validate_outputs(tables, summary)


if __name__ == "__main__":
    main()
