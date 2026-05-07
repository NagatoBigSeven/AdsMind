"""Build CMU20 and OCD62 cost-vs-depth method comparison tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import BACKEND_KEYS, backend_identity, backend_result_dir, summary_metadata

RESULTS_ROOT = ROOT / "research" / "results"
BASIC_ROOT = RESULTS_ROOT / "basic_experiments"
BASIC_SUMMARY_DIR = BASIC_ROOT / "summaries"
OCD62_MANIFEST = ROOT / "datasets" / "ocd62" / "ocd62_manifest.csv"

BACKENDS = list(BACKEND_KEYS)
VARIANT_ALIASES = {
    "one_shot": {"one_shot", "single_shot"},
}

DATASETS = {
    "cmu20": {
        "n_cases": 20,
        "case_width": 2,
    },
    "ocd62": {
        "n_cases": 62,
        "case_width": 3,
    },
}


def dataset_summary_dir(dataset: str) -> Path:
    return BASIC_ROOT / dataset / "summaries"


def backend_dir(dataset: str, backend: str) -> Path:
    return BASIC_ROOT / dataset / backend_result_dir(backend)


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
    return backend_dir(dataset, backend) / variant / case_id / "result.json"


def backend_column(backend: str) -> str:
    return backend_result_dir(backend)


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
    path = backend_dir(dataset, backend) / "all_variants_summary.csv"
    df = read_csv(path)
    accepted_variants = VARIANT_ALIASES.get(variant, {variant})
    subset = df[df["variant"].isin(accepted_variants)].copy()
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


def value_from_row(row: pd.Series, key: str, fallback: object = "") -> object:
    value = row.get(key, fallback)
    if pd.isna(value):
        return ""
    return value


def build_ablation_4backend(dataset: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case_id in case_ids(dataset):
        for backend in BACKENDS:
            path = backend_dir(dataset, backend) / "all_variants_summary.csv"
            df = read_csv(path)
            df["case_id"] = df["case_id"].map(lambda value: pad_case_id(value, dataset))
            for _, row in df[df["case_id"] == case_id].iterrows():
                rows.append(
                    {
                        "case_id": case_id,
                        **summary_metadata(backend_identity(backend)),
                        "variant": value_from_row(row, "variant"),
                        "best_energy_eV": value_from_row(row, "best_energy"),
                        "success": "TRUE" if to_success(pd.Series([row.get("success", "")])).iloc[0] else "FALSE",
                        "run_path": str(
                            (
                                backend_dir(dataset, backend)
                                / str(value_from_row(row, "variant"))
                                / case_id
                            ).relative_to(ROOT)
                        ),
                        "iterations": value_from_row(row, "iterations", value_from_row(row, "iteration_count")),
                        "wasted_iterations": value_from_row(row, "wasted_iterations", value_from_row(row, "calc_failure_count")),
                        "waste_ratio": value_from_row(row, "waste_ratio"),
                        "slip_count": value_from_row(row, "slip_count", value_from_row(row, "chemical_slip_count")),
                        "dissociation_count": value_from_row(row, "dissociation_count"),
                        "tokens_used": value_from_row(row, "tokens_used"),
                    }
                )
    fields = [
        "case_id",
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
    ]
    return pd.DataFrame(rows, columns=fields)


def add_adsmind_columns(table: pd.DataFrame, dataset: str, variant: str, prefix: str) -> None:
    for backend in BACKENDS:
        rows = load_adsmind_backend_rows(dataset, backend, variant).set_index("case_id")
        column_backend = backend_column(backend)
        for metric in ["energy", "relax", "success"]:
            table[f"{prefix}_{column_backend}_{metric}"] = table["case_id"].map(rows[metric])

    energy_cols = [f"{prefix}_{backend_column(backend)}_energy" for backend in BACKENDS]
    relax_cols = [f"{prefix}_{backend_column(backend)}_relax" for backend in BACKENDS]
    success_cols = [f"{prefix}_{backend_column(backend)}_success" for backend in BACKENDS]

    table[f"{prefix}_energy_best4"] = table[energy_cols].min(axis=1, skipna=True)
    table[f"{prefix}_energy_mean4"] = table[energy_cols].mean(axis=1, skipna=True)
    table[f"{prefix}_best4"] = table[f"{prefix}_energy_best4"]
    table[f"{prefix}_mean4"] = table[f"{prefix}_energy_mean4"]
    table[f"{prefix}_energy"] = table[f"{prefix}_energy_mean4"]
    table[f"{prefix}_relax"] = table[relax_cols].mean(axis=1, skipna=True)
    table[f"{prefix}_success"] = table[success_cols].mean(axis=1, skipna=True)
    table[f"{prefix}_success_any4"] = table[success_cols].fillna(False).any(axis=1)
    table[f"{prefix}_success_all4"] = table[success_cols].fillna(False).all(axis=1)


def add_random_columns(table: pd.DataFrame, dataset: str) -> None:
    path = BASIC_ROOT / dataset / "baselines" / "random_n20" / "summary.csv"
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
    path = BASIC_ROOT / dataset / "baselines" / "heuristic" / "summary.csv"
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

    baseline_dir = (
        BASIC_ROOT
        / dataset
        / "baselines"
        / "adsorb-agent"
        / "adsorb-agent_gpt54_mace_mp0_small_5config"
    )
    path = baseline_dir / "summary.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{dataset}: expected matched Adsorb-Agent 5-config summary at {path.relative_to(ROOT)}"
        )

    df = read_csv(path)
    df["case_id"] = df["case_id"].map(lambda value: pad_case_id(value, dataset))
    df["energy"] = to_num(df["best_adsorption_energy_eV"])
    df["relax"] = to_num(df["adsorbagent_configs_tested"]).fillna(0)
    df["success"] = to_success(df["status"]) & (to_num(df["valid_traj_count"]) > 0) & df["energy"].notna()
    df.loc[~df["success"], "energy"] = np.nan
    rows = df.set_index("case_id")

    table["adsorbagent_energy"] = table["case_id"].map(rows["energy"])
    table["adsorbagent_relax"] = table["case_id"].map(rows["relax"])
    table["adsorbagent_success"] = table["case_id"].map(rows["success"]).astype(float)


def build_dataset_table(dataset: str) -> pd.DataFrame:
    rows = [load_metadata(dataset, case_id) for case_id in case_ids(dataset)]
    table = pd.DataFrame(rows)

    add_adsmind_columns(table, dataset, "one_shot", "adsmind_1shot")
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
    BASIC_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    (BASIC_SUMMARY_DIR / "method_comparison_table.md").write_text("\n".join(md_lines), encoding="utf-8")

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
    (BASIC_SUMMARY_DIR / "method_comparison_table.tex").write_text("\n".join(tex_lines), encoding="utf-8")


def summarize_cross_dataset_basic_tests(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset, table in tables.items():
        full_success_cols = [f"adsmind_full_{backend_column(backend)}_success" for backend in BACKENDS]
        shot_success_cols = [f"adsmind_1shot_{backend_column(backend)}_success" for backend in BACKENDS]
        full_energy_cols = [f"adsmind_full_{backend_column(backend)}_energy" for backend in BACKENDS]
        shot_energy_cols = [f"adsmind_1shot_{backend_column(backend)}_energy" for backend in BACKENDS]

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


def write_basic_test_summary(basic: pd.DataFrame) -> None:
    BASIC_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    basic.to_csv(BASIC_SUMMARY_DIR / "full_vs_one_shot_summary.csv", index=False)


def validate_outputs(tables: dict[str, pd.DataFrame], summary: pd.DataFrame) -> None:
    for dataset, expected in {"cmu20": 20, "ocd62": 62}.items():
        observed = len(tables[dataset])
        if observed != expected:
            raise ValueError(f"{dataset}: expected {expected} rows, observed {observed}")
    if len(summary) != 10:
        raise ValueError(f"Expected 10 main summary rows, observed {len(summary)}")


def main() -> None:
    BASIC_ROOT.mkdir(parents=True, exist_ok=True)
    BASIC_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    tables = {dataset: build_dataset_table(dataset) for dataset in DATASETS}
    for dataset, table in tables.items():
        output_dir = dataset_summary_dir(dataset)
        output_dir.mkdir(parents=True, exist_ok=True)
        public_path = output_dir / "method_comparison.csv"
        table.to_csv(public_path, index=False)
        print(f"Wrote {public_path.relative_to(ROOT)} ({len(table)} rows)")
        if dataset == "cmu20":
            ablation_path = output_dir / "ablation_4backend.csv"
            build_ablation_4backend(dataset).to_csv(ablation_path, index=False)
            print(f"Wrote {ablation_path.relative_to(ROOT)}")

    summary = summarize_tables(tables)
    summary.to_csv(BASIC_SUMMARY_DIR / "method_comparison_summary.csv", index=False)
    write_publication_tables(summary)
    write_basic_test_summary(summarize_cross_dataset_basic_tests(tables))
    validate_outputs(tables, summary)


if __name__ == "__main__":
    main()
