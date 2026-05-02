"""Prepare a representative OCD-GMAE subset manifest for JCIM-facing one-shot runs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

from research.agent_eval.common import resolve_repo_path
from research.agent_eval.prepare_ocd_gmae import (
    DEFAULT_LMDB_PATH,
    DEFAULT_PRIORITY_SMILES,
    OCDCandidate,
    load_candidates,
    write_outputs,
)

DEFAULT_MANIFEST_PATH = Path("research/agent_eval/manifests/ocd_gmae_representative50_manifest.csv")
DEFAULT_SLAB_DIR = Path("research/agent_eval/generated_slabs/ocd_gmae_representative50")
DEFAULT_SUMMARY_PATH = Path("research/agent_eval/manifests/ocd_gmae_representative50_manifest_selection.json")
DEFAULT_CASES = 50
DEFAULT_ENERGY_BINS = 5
DEFAULT_MAX_PER_SMILES = 5


@dataclass(frozen=True)
class TaggedCandidate:
    """OCD candidate plus a global energy-bin label for stratified sampling."""

    candidate: OCDCandidate
    energy_bin: int


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a representative OCD-GMAE manifest for JCIM-facing one-shot experiments."
    )
    parser.add_argument("--lmdb-path", default=str(DEFAULT_LMDB_PATH), help="Path to OCD-GMAE data.lmdb")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH), help="Output CSV manifest path")
    parser.add_argument("--slab-dir", default=str(DEFAULT_SLAB_DIR), help="Directory for generated slab extxyz files")
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH), help="Output JSON summary path")
    parser.add_argument("--max-cases", type=int, default=DEFAULT_CASES, help="Number of representative cases to export")
    parser.add_argument(
        "--max-slab-atoms",
        type=int,
        default=200,
        help="Exclude bare slabs with more than this many atoms",
    )
    parser.add_argument(
        "--priority-smiles",
        default=",".join(DEFAULT_PRIORITY_SMILES),
        help="Comma-separated adsorbate inclusion list",
    )
    parser.add_argument(
        "--energy-bins",
        type=int,
        default=DEFAULT_ENERGY_BINS,
        help="Number of global adsorption-energy bins for representative balancing",
    )
    parser.add_argument(
        "--max-per-smiles",
        type=int,
        default=DEFAULT_MAX_PER_SMILES,
        help="Soft cap on how many cases any one adsorbate contributes",
    )
    return parser.parse_args(argv)


def proportional_targets(
    counts: Dict[str, int],
    total: int,
    *,
    minimums: Optional[Dict[str, int]] = None,
    maximums: Optional[Dict[str, int]] = None,
) -> dict[str, int]:
    """Allocate integer quotas with largest-remainder rounding."""

    minimums = minimums or {}
    maximums = maximums or {}
    keys = [key for key, value in counts.items() if value > 0]
    targets = {key: min(minimums.get(key, 0), counts[key]) for key in keys}
    assigned = sum(targets.values())
    if assigned > total:
        raise ValueError("Minimum quotas exceed requested total.")

    remaining = total - assigned
    if remaining == 0:
        return targets

    residual_capacity = {
        key: max(0, min(maximums.get(key, counts[key]), counts[key]) - targets[key])
        for key in keys
    }
    available_capacity = sum(residual_capacity.values())
    if available_capacity < remaining:
        raise ValueError("Not enough residual capacity to satisfy representative quota.")

    total_weight = float(sum(counts[key] for key in keys))
    if total_weight <= 0:
        raise ValueError("Cannot allocate quotas from an empty candidate pool.")

    raw_allocations = {}
    for key in keys:
        share = remaining * counts[key] / total_weight
        extra = min(residual_capacity[key], int(share))
        raw_allocations[key] = share
        targets[key] += extra
        residual_capacity[key] -= extra

    leftover = total - sum(targets.values())
    if leftover <= 0:
        return targets

    remainders = sorted(
        (
            raw_allocations[key] - int(raw_allocations[key]),
            counts[key],
            key,
        )
        for key in keys
        if residual_capacity[key] > 0
    )
    while leftover > 0:
        allocated = False
        for _, _, key in reversed(remainders):
            if residual_capacity[key] <= 0:
                continue
            targets[key] += 1
            residual_capacity[key] -= 1
            leftover -= 1
            allocated = True
            if leftover == 0:
                break
        if not allocated:
            raise ValueError("Failed to distribute all representative quotas.")

    return targets


def assign_energy_bins(candidates: Sequence[OCDCandidate], bin_count: int) -> list[TaggedCandidate]:
    """Assign near-equal-count bins over the global y_relaxed ranking."""

    if bin_count <= 0:
        raise ValueError("energy-bins must be positive")
    ordered = sorted(
        candidates,
        key=lambda candidate: (candidate.y_relaxed, candidate.surface_formula, candidate.source_key),
    )
    total = len(ordered)
    tagged: list[TaggedCandidate] = []
    for index, candidate in enumerate(ordered):
        energy_bin = min(bin_count - 1, index * bin_count // max(total, 1))
        tagged.append(TaggedCandidate(candidate=candidate, energy_bin=energy_bin))
    return tagged


def _ideal_rank(slot: int, quota: int) -> float:
    if quota <= 1:
        return 0.5
    return slot / float(quota - 1)


def _rank_fraction(index: int, size: int) -> float:
    if size <= 1:
        return 0.5
    return index / float(size - 1)


def _minima_by_smiles(counts: Dict[str, int]) -> dict[str, int]:
    minima = {smiles: 1 for smiles, count in counts.items() if count > 0}
    for smiles in ("[H]", "[OH]"):
        if counts.get(smiles, 0) >= 2:
            minima[smiles] = 2
    return minima


def _quotas_by_smiles(
    tagged_candidates: Sequence[TaggedCandidate],
    priority_smiles: Sequence[str],
    max_cases: int,
    max_per_smiles: int,
) -> dict[str, int]:
    grouped = Counter(tagged.candidate.mapped_smiles for tagged in tagged_candidates)
    ordered_counts = {smiles: grouped[smiles] for smiles in priority_smiles if grouped.get(smiles, 0) > 0}
    minimums = _minima_by_smiles(ordered_counts)
    maximums = {
        smiles: min(max_per_smiles, count)
        for smiles, count in ordered_counts.items()
    }
    for smiles in ("[H]", "[OH]"):
        if smiles in maximums:
            maximums[smiles] = min(maximums[smiles], 3)
    return proportional_targets(ordered_counts, max_cases, minimums=minimums, maximums=maximums)


def select_representative_candidates(
    tagged_candidates: Sequence[TaggedCandidate],
    *,
    priority_smiles: Sequence[str],
    max_cases: int,
    max_per_smiles: int,
    energy_bins: int,
) -> tuple[list[OCDCandidate], dict[str, object]]:
    """Select a balanced 50-case representative subset."""

    if max_cases <= 0:
        return [], {
            "quota_by_smiles": {},
            "target_counts_by_surface_family": {},
            "target_counts_by_selection_bucket": {},
            "target_counts_by_energy_bin": {},
        }

    quota_by_smiles = _quotas_by_smiles(tagged_candidates, priority_smiles, max_cases, max_per_smiles)
    family_targets = proportional_targets(
        dict(Counter(tagged.candidate.surface_family for tagged in tagged_candidates)),
        max_cases,
    )
    bucket_targets = proportional_targets(
        dict(Counter(tagged.candidate.selection_bucket for tagged in tagged_candidates)),
        max_cases,
    )
    energy_targets = proportional_targets(
        {str(index): count for index, count in Counter(tagged.energy_bin for tagged in tagged_candidates).items()},
        max_cases,
    )

    grouped: dict[str, list[TaggedCandidate]] = {smiles: [] for smiles in priority_smiles}
    for tagged in tagged_candidates:
        grouped.setdefault(tagged.candidate.mapped_smiles, []).append(tagged)
    for values in grouped.values():
        values.sort(
            key=lambda tagged: (
                tagged.candidate.y_relaxed,
                tagged.candidate.surface_formula,
                tagged.candidate.source_key,
            )
        )

    selected: list[TaggedCandidate] = []
    used_source_keys: set[str] = set()
    seen_formulas: set[str] = set()
    counts_by_family: Counter[str] = Counter()
    counts_by_bucket: Counter[str] = Counter()
    counts_by_energy: Counter[str] = Counter()
    counts_by_smiles: Counter[str] = Counter()

    def select_one(pool: Sequence[TaggedCandidate], *, ideal_rank: float, slot_index: int) -> Optional[TaggedCandidate]:
        best: Optional[tuple[float, float, float, float, str, TaggedCandidate]] = None
        size = len(pool)
        for index, tagged in enumerate(pool):
            candidate = tagged.candidate
            if candidate.source_key in used_source_keys:
                continue
            family = candidate.surface_family
            bucket = candidate.selection_bucket
            energy_key = str(tagged.energy_bin)
            formula_bonus = 1.25 if candidate.surface_formula not in seen_formulas else 0.0
            family_deficit = max(family_targets.get(family, 0) - counts_by_family[family], 0)
            bucket_deficit = max(bucket_targets.get(bucket, 0) - counts_by_bucket[bucket], 0)
            energy_deficit = max(energy_targets.get(energy_key, 0) - counts_by_energy[energy_key], 0)
            rank_penalty = abs(_rank_fraction(index, size) - ideal_rank)
            slot_penalty = counts_by_smiles[candidate.mapped_smiles] - slot_index
            score = (
                float(family_deficit + bucket_deficit + energy_deficit) + formula_bonus,
                -rank_penalty,
                -slot_penalty,
                -candidate.bare_slab_atoms,
                candidate.source_key,
            )
            if best is None or score > best[:-1]:
                best = (*score, tagged)
        return None if best is None else best[-1]

    for smiles in priority_smiles:
        quota = quota_by_smiles.get(smiles, 0)
        if quota <= 0:
            continue
        pool = grouped.get(smiles, [])
        for slot in range(quota):
            picked = select_one(pool, ideal_rank=_ideal_rank(slot, quota), slot_index=slot)
            if picked is None:
                break
            candidate = picked.candidate
            selected.append(picked)
            used_source_keys.add(candidate.source_key)
            seen_formulas.add(candidate.surface_formula)
            counts_by_family[candidate.surface_family] += 1
            counts_by_bucket[candidate.selection_bucket] += 1
            counts_by_energy[str(picked.energy_bin)] += 1
            counts_by_smiles[candidate.mapped_smiles] += 1
            if len(selected) >= max_cases:
                break
        if len(selected) >= max_cases:
            break

    if len(selected) < max_cases:
        remaining_pool = sorted(
            (tagged for tagged in tagged_candidates if tagged.candidate.source_key not in used_source_keys),
            key=lambda tagged: (
                -max(
                    family_targets.get(tagged.candidate.surface_family, 0) - counts_by_family[tagged.candidate.surface_family],
                    0,
                )
                - max(
                    bucket_targets.get(tagged.candidate.selection_bucket, 0) - counts_by_bucket[tagged.candidate.selection_bucket],
                    0,
                )
                - max(
                    energy_targets.get(str(tagged.energy_bin), 0) - counts_by_energy[str(tagged.energy_bin)],
                    0,
                ),
                tagged.candidate.surface_formula in seen_formulas,
                tagged.candidate.y_relaxed,
                tagged.candidate.source_key,
            ),
        )
        for tagged in remaining_pool:
            candidate = tagged.candidate
            selected.append(tagged)
            used_source_keys.add(candidate.source_key)
            seen_formulas.add(candidate.surface_formula)
            counts_by_family[candidate.surface_family] += 1
            counts_by_bucket[candidate.selection_bucket] += 1
            counts_by_energy[str(tagged.energy_bin)] += 1
            counts_by_smiles[candidate.mapped_smiles] += 1
            if len(selected) >= max_cases:
                break

    selected_candidates = [tagged.candidate for tagged in selected[:max_cases]]
    selection_summary = {
        "quota_by_smiles": quota_by_smiles,
        "selected_counts_by_smiles": dict(counts_by_smiles),
        "target_counts_by_surface_family": family_targets,
        "selected_counts_by_surface_family": dict(counts_by_family),
        "target_counts_by_selection_bucket": bucket_targets,
        "selected_counts_by_selection_bucket": dict(counts_by_bucket),
        "target_counts_by_energy_bin": energy_targets,
        "selected_counts_by_energy_bin": dict(counts_by_energy),
    }
    return selected_candidates, selection_summary


def build_summary_payload(
    *,
    base_summary: dict[str, object],
    tagged_candidates: Sequence[TaggedCandidate],
    selection_summary: dict[str, object],
) -> dict[str, object]:
    tagged_by_key = {tagged.candidate.source_key: tagged.energy_bin for tagged in tagged_candidates}
    selected_cases = []
    for row in base_summary["selected_cases"]:
        copied = dict(row)
        copied["energy_bin"] = tagged_by_key.get(copied["source_key"])
        selected_cases.append(copied)
    return {
        **base_summary,
        "selection_mode": "representative_jcim_one_shot",
        "selection_policy": {
            "goals": [
                "cover all supported adsorbates at least once",
                "keep H and OH duplicated because they bridge the CMU overlap subset",
                "approximate the full 287-case pool across surface family, adsorbate bucket, and global energy bins",
                "avoid repeated surface formulas when alternatives exist",
            ],
        },
        "pool_candidate_count": len(tagged_candidates),
        **selection_summary,
        "selected_cases": selected_cases,
    }


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    lmdb_path = Path(args.lmdb_path).expanduser().resolve()
    manifest_path = resolve_repo_path(args.manifest_path, repo_root=repo_root)
    slab_dir = resolve_repo_path(args.slab_dir, repo_root=repo_root)
    summary_path = resolve_repo_path(args.summary_path, repo_root=repo_root)
    priority_smiles = [value.strip() for value in args.priority_smiles.split(",") if value.strip()]

    try:
        candidates = load_candidates(
            lmdb_path=lmdb_path,
            priority_smiles=priority_smiles,
            max_slab_atoms=args.max_slab_atoms,
        )
    except RuntimeError as exc:
        print(str(exc))
        return 2

    tagged_candidates = assign_energy_bins(candidates, args.energy_bins)
    selected, selection_summary = select_representative_candidates(
        tagged_candidates,
        priority_smiles=priority_smiles,
        max_cases=args.max_cases,
        max_per_smiles=args.max_per_smiles,
        energy_bins=args.energy_bins,
    )
    base_summary = write_outputs(
        selected=selected,
        manifest_path=manifest_path,
        slab_dir=slab_dir,
        repo_root=repo_root,
        summary_path=None,
    )
    full_summary = build_summary_payload(
        base_summary=base_summary,
        tagged_candidates=tagged_candidates,
        selection_summary=selection_summary,
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(full_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "lmdb_path": str(lmdb_path),
                "pool_candidate_count": len(candidates),
                "selected_case_count": full_summary["selected_case_count"],
                "selected_counts_by_smiles": full_summary["selected_counts_by_smiles"],
                "selected_counts_by_surface_family": full_summary["selected_counts_by_surface_family"],
                "selected_counts_by_selection_bucket": full_summary["selected_counts_by_selection_bucket"],
                "selected_counts_by_energy_bin": full_summary["selected_counts_by_energy_bin"],
                "manifest_path": str(manifest_path),
                "summary_path": str(summary_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
