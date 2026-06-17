"""Normalize provenance columns in advanced experiment summary CSVs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import (
    BACKEND_KEYS,
    backend_identity,
    backend_result_dir,
    identity_from_label,
    summary_metadata,
)


PROVENANCE_FIELDS = [
    "backend_key",
    "backend",
    "llm_model",
    "force_field",
    "calculator_backend",
    "force_field_model",
    "force_field_size",
]

RESULTS = ROOT / "research" / "results"
BASIC = RESULTS / "basic_experiments"
ADVANCED = RESULTS / "advanced_experiments"
MECHANISM = ADVANCED / "ablation_and_chemical_slip_diagnostics" / "ablation_effects"

BACKEND_ALIASES = {
    "gpt": "gpt",
    "gpt54_mace_mp0_small": "gpt",
    "claude": "claude",
    "claude_sonnet46_mace_mp0_small": "claude",
    "gemini": "gemini",
    "gemini25pro_mace_mp0_small": "gemini",
    "grok": "grok",
    "grok4": "grok",
    "grok4_mace_mp0_small": "grok",
    "claude_sonnet46_mace_mp0_small_sonnet46_mace_mp0_small": "claude",
}

SHORT_BACKEND_VALUES = set(BACKEND_ALIASES)


def backend_key_for_alias(value: str) -> str | None:
    return BACKEND_ALIASES.get(value)


def full_backend_for_alias(value: str) -> str | None:
    key = backend_key_for_alias(value)
    return backend_result_dir(key) if key else None


def backend_metadata_by_full_dir() -> dict[str, dict[str, str]]:
    return {
        backend_result_dir(key): summary_metadata(backend_identity(key))
        for key in BACKEND_KEYS
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value: object) -> float | None:
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def success(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "success"}


def dataset_case_width(dataset: str) -> int:
    return 2 if dataset == "cmu20" else 3


def ablation_summary(dataset: str) -> list[dict[str, str]]:
    path = BASIC / dataset / "summaries" / "ablation_4backend.csv"
    if not path.exists():
        path = BASIC / "summaries" / f"{dataset}_ablation_4backend.csv"
    rows = read_csv(path)
    width = dataset_case_width(dataset)
    for row in rows:
        row["case_id"] = row["case_id"].zfill(width)
    return rows


def write_reach_full() -> None:
    rows: list[dict[str, object]] = []
    for dataset in ("cmu20", "ocd62"):
        data = ablation_summary(dataset)
        full_by_backend_case = {
            (row["backend_key"], row["case_id"]): parse_float(row["best_energy_eV"])
            for row in data
            if row["variant"] == "full" and success(row["success"])
        }
        for row in data:
            if row["variant"] == "full" or not success(row["success"]):
                continue
            full_energy = full_by_backend_case.get((row["backend_key"], row["case_id"]))
            variant_energy = parse_float(row["best_energy_eV"])
            if full_energy is None or variant_energy is None:
                continue
            delta = variant_energy - full_energy
            rows.append(
                {
                    "dataset": dataset,
                    "case_id": row["case_id"],
                    **{field: row.get(field, "") for field in PROVENANCE_FIELDS},
                    "variant": row["variant"],
                    "full_energy_eV": f"{full_energy:.12g}",
                    "variant_energy_eV": f"{variant_energy:.12g}",
                    "delta_variant_minus_full_eV": f"{delta:.12g}",
                    "within_0.01eV_of_full": "TRUE" if delta <= 0.01 else "FALSE",
                }
            )
    write_csv(
        MECHANISM / "reach_full_within_0.01eV.csv",
        rows,
        ["dataset", "case_id", *PROVENANCE_FIELDS, "variant", "full_energy_eV", "variant_energy_eV", "delta_variant_minus_full_eV", "within_0.01eV_of_full"],
    )


def write_variant_delta_statistics() -> None:
    """Write paired variant-minus-Full statistics with full backend provenance."""
    rows: list[dict[str, object]] = []
    stats: dict[str, dict[str, object]] = {}
    try:
        from scipy.stats import wilcoxon
    except Exception:
        wilcoxon = None

    for dataset in ("cmu20", "ocd62"):
        data = ablation_summary(dataset)
        full_by_backend_case = {
            (row["backend_key"], row["case_id"]): row
            for row in data
            if row["variant"] == "full" and success(row["success"])
        }
        for row in data:
            if row["variant"] == "full" or not success(row["success"]):
                continue
            full_row = full_by_backend_case.get((row["backend_key"], row["case_id"]))
            if not full_row:
                continue
            full_energy = parse_float(full_row.get("best_energy_eV"))
            variant_energy = parse_float(row.get("best_energy_eV"))
            if full_energy is None or variant_energy is None:
                continue
            delta = variant_energy - full_energy
            rows.append(
                {
                    "dataset": dataset,
                    "case_id": row["case_id"],
                    **{field: row.get(field, "") for field in PROVENANCE_FIELDS},
                    "variant": row["variant"],
                    "full_energy_eV": full_energy,
                    "variant_energy_eV": variant_energy,
                    "delta_variant_minus_full_eV": delta,
                }
            )

    variants = sorted({str(row["variant"]) for row in rows})
    for dataset in ("cmu20", "ocd62"):
        for variant in variants:
            paired = [row for row in rows if row["dataset"] == dataset and row["variant"] == variant]
            deltas = [float(row["delta_variant_minus_full_eV"]) for row in paired]
            if not deltas:
                continue
            wilcoxon_statistic = ""
            wilcoxon_p_value = ""
            if wilcoxon is not None and any(abs(value) > 1e-12 for value in deltas):
                try:
                    result = wilcoxon(deltas)
                    wilcoxon_statistic = f"{float(result.statistic):.12g}"
                    wilcoxon_p_value = f"{float(result.pvalue):.12g}"
                except Exception:
                    pass
            key = f"{dataset}:{variant}"
            stats[key] = {
                "dataset": dataset,
                "variant": variant,
                "paired_runs": len(deltas),
                "mean_delta_variant_minus_full_eV": f"{mean(deltas):.12g}",
                "median_delta_variant_minus_full_eV": f"{median(deltas):.12g}",
                "mean_abs_delta_eV": f"{mean(abs(value) for value in deltas):.12g}",
                "worse_than_full_count": sum(1 for value in deltas if value > 0.01),
                "within_0.01eV_count": sum(1 for value in deltas if abs(value) <= 0.01),
                "better_than_full_count": sum(1 for value in deltas if value < -0.01),
                "wilcoxon_statistic": wilcoxon_statistic,
                "wilcoxon_p_value": wilcoxon_p_value,
                "paired_rows": paired,
            }

    write_csv(
        MECHANISM / "variant_delta_statistics.csv",
        [
            {key: value for key, value in payload.items() if key != "paired_rows"}
            for payload in stats.values()
        ],
        [
            "dataset",
            "variant",
            "paired_runs",
            "mean_delta_variant_minus_full_eV",
            "median_delta_variant_minus_full_eV",
            "mean_abs_delta_eV",
            "worse_than_full_count",
            "within_0.01eV_count",
            "better_than_full_count",
            "wilcoxon_statistic",
            "wilcoxon_p_value",
        ],
    )
    nested: dict[str, dict[str, object]] = {}
    for payload in stats.values():
        nested.setdefault(str(payload["dataset"]), {})[str(payload["variant"])] = payload
    (MECHANISM / "variant_delta_statistics.json").write_text(
        json.dumps(nested, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_cross_backend_agreement() -> None:
    rows: list[dict[str, object]] = []
    for dataset in ("cmu20", "ocd62"):
        grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in ablation_summary(dataset):
            if not success(row["success"]):
                continue
            grouped.setdefault((row["case_id"], row["variant"]), []).append(row)
        for (case_id, variant), group in sorted(grouped.items()):
            energies = [parse_float(row["best_energy_eV"]) for row in group]
            energies = [value for value in energies if value is not None]
            if not energies:
                continue
            backend_names = [row["backend"] for row in group]
            rows.append(
                {
                    "dataset": dataset,
                    "case_id": case_id,
                    "variant": variant,
                    "backend_count": len(BACKEND_KEYS),
                    "success_backend_count": len(group),
                    "min_energy_eV": f"{min(energies):.12g}",
                    "max_energy_eV": f"{max(energies):.12g}",
                    "range_energy_eV": f"{(max(energies) - min(energies)):.12g}",
                    "mean_energy_eV": f"{mean(energies):.12g}",
                    "success_backends": ";".join(backend_names),
                }
            )
    write_csv(
        MECHANISM / "cross_backend_agreement.csv",
        rows,
        ["dataset", "case_id", "variant", "backend_count", "success_backend_count", "min_energy_eV", "max_energy_eV", "range_energy_eV", "mean_energy_eV", "success_backends"],
    )


def provenance_for_row(row: dict[str, str]) -> dict[str, str]:
    backend_value = row.get("backend", "")
    full_backend = full_backend_for_alias(backend_value) or backend_value
    if full_backend in {backend_result_dir(key) for key in BACKEND_KEYS}:
        identity = next(backend_identity(key) for key in BACKEND_KEYS if backend_result_dir(key) == full_backend)
    else:
        identity = identity_from_label(backend_value or row.get("backend_key", ""))
    return summary_metadata(identity) if identity is not None else {field: row.get(field, "") for field in PROVENANCE_FIELDS}


def normalize_backend_csv(path: Path) -> None:
    rows = read_csv(path)
    if not rows:
        return
    old_fields = list(rows[0].keys())
    normalized = []
    for row in rows:
        metadata = provenance_for_row(row)
        clean = {key: value for key, value in row.items() if key not in PROVENANCE_FIELDS}
        if clean.get("variant") == "single_shot":
            clean["variant"] = "one_shot"
        normalized.append({**metadata, **clean})
    fields = [field for field in old_fields if field not in PROVENANCE_FIELDS and field != "backend"]
    write_csv(path, normalized, [*PROVENANCE_FIELDS, *fields])


def canonicalize_backend_value(value: str) -> str:
    return full_backend_for_alias(value) or value


def canonicalize_backend_key(value: str) -> str:
    if value.endswith("_single_shot"):
        value = f"{value[: -len('_single_shot')]}_one_shot"
    full = full_backend_for_alias(value)
    if full is not None:
        return full
    for alias in sorted(SHORT_BACKEND_VALUES, key=len, reverse=True):
        if value.startswith(f"{alias}_"):
            mapped = full_backend_for_alias(alias)
            if mapped is not None:
                return f"{mapped}_{value[len(alias) + 1:]}"
    return value


def canonicalize_text(value: str) -> str:
    if value == "single_shot":
        return "one_shot"
    return value


def canonicalize_metric_keys(obj: object) -> object:
    if isinstance(obj, dict):
        converted: dict[str, object] = {}
        for key, value in obj.items():
            if key == "backend_metadata":
                continue
            new_key = canonicalize_backend_key(key)
            if new_key.endswith("_n"):
                base = new_key[:-2]
                new_key = f"{canonicalize_backend_key(base)}_n"
            converted[new_key] = canonicalize_metric_keys(value)
        return converted
    if isinstance(obj, list):
        return [canonicalize_metric_keys(item) for item in obj]
    if isinstance(obj, str):
        return canonicalize_text(obj)
    return obj


def canonicalize_record_backends(obj: object) -> object:
    if isinstance(obj, dict):
        converted = {key: canonicalize_record_backends(value) for key, value in obj.items()}
        variant = converted.get("variant")
        if variant == "single_shot":
            converted["variant"] = "one_shot"
        backend = converted.get("backend")
        if isinstance(backend, str):
            key = backend_key_for_alias(backend)
            metadata = summary_metadata(backend_identity(key)) if key else None
            if metadata is not None:
                converted.update(metadata)
        else:
            key = converted.get("backend_key")
            if isinstance(key, str) and key in BACKEND_KEYS:
                converted.update(summary_metadata(backend_identity(key)))
        return converted
    if isinstance(obj, list):
        return [canonicalize_record_backends(item) for item in obj]
    return obj


def normalize_json(path: Path, *, canonicalize_records: bool = False, canonicalize_keys: bool = False) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if canonicalize_keys:
        data = canonicalize_metric_keys(data)
    if canonicalize_records:
        data = canonicalize_record_backends(data)
    data["backend_metadata"] = backend_metadata_by_full_dir()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_iteration_convergence_summary(path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    backends = data.get("backends", {})
    normalized: dict[str, object] = {}
    if isinstance(backends, dict):
        for key, value in backends.items():
            full = canonicalize_backend_key(key)
            if isinstance(value, dict):
                metadata = summary_metadata(backend_identity(backend_key_for_alias(full))) if backend_key_for_alias(full) else {}
                normalized[full] = {**metadata, **value}
            else:
                normalized[full] = value
    data["backends"] = normalized
    data["backend_metadata"] = backend_metadata_by_full_dir()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_slip_analysis_csv(path: Path) -> None:
    rows = read_csv(path)
    if not rows:
        return
    rename: dict[str, str] = {}
    for field in rows[0]:
        for alias in sorted(SHORT_BACKEND_VALUES, key=len, reverse=True):
            if field == alias or field.startswith(f"{alias}_"):
                full = full_backend_for_alias(alias)
                if full:
                    rename[field] = field.replace(alias, full, 1)
                break
    normalized = []
    for row in rows:
        normalized.append({rename.get(key, key): value for key, value in row.items()})
    fields = [rename.get(field, field) for field in rows[0]]
    write_csv(path, normalized, fields)


def normalize_outlier_patch_csv(path: Path) -> None:
    if not path.exists():
        return
    rows = read_csv(path)
    if not rows:
        return
    normalized = []
    for row in rows:
        metadata = provenance_for_row(row)
        clean = {key: value for key, value in row.items() if key not in PROVENANCE_FIELDS}
        if clean.get("variant") == "single_shot":
            clean["variant"] = "one_shot"
        normalized.append({**metadata, **clean})
    old_fields = list(rows[0])
    fields = [field for field in old_fields if field not in PROVENANCE_FIELDS and field != "backend"]
    write_csv(path, normalized, [*PROVENANCE_FIELDS, *fields])


def main() -> int:
    write_reach_full()
    write_variant_delta_statistics()
    write_cross_backend_agreement()
    for path in [
        ADVANCED / "ablation_and_chemical_slip_diagnostics" / "chemical_slip_interpretability" / "cmu20" / "case19_trajectory.csv",
        ADVANCED / "case_studies" / "iteration_convergence" / "cmu20" / "all_backends" / "full" / "iteration_convergence.csv",
    ]:
        normalize_backend_csv(path)
    normalize_slip_analysis_csv(
        ADVANCED / "ablation_and_chemical_slip_diagnostics" / "chemical_slip_interpretability" / "cmu20" / "slip_analysis.csv"
    )
    normalize_outlier_patch_csv(
        ADVANCED / "reproducibility" / "ocd62_overlap12_rerun" / "summaries" / "grok_ocd16_outlier_patch.csv"
    )
    for path in [
        ADVANCED / "ablation_and_chemical_slip_diagnostics" / "chemical_slip_interpretability" / "cmu20" / "slip_analysis.json",
        MECHANISM / "variant_delta_statistics.json",
    ]:
        normalize_json(path, canonicalize_keys=True)
    normalize_json(
        ADVANCED / "ablation_and_chemical_slip_diagnostics" / "chemical_slip_interpretability" / "cmu20" / "case19_trajectory.json",
        canonicalize_records=True,
        canonicalize_keys=True,
    )
    normalize_iteration_convergence_summary(
        ADVANCED / "case_studies" / "iteration_convergence" / "cmu20" / "all_backends" / "full" / "iteration_convergence_summary.json"
    )
    print("advanced provenance normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
