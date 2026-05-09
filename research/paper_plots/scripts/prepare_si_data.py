#!/usr/bin/env python3
"""
Prepare SI Figure data from results/ raw data.

Reads original data from research/results/ and writes processed versions to
research/results/processed/si_figures/, remapping backend names from long to
short form to match the format expected by the SI notebooks.

Usage:
    python research/paper_plots/scripts/prepare_si_data.py

Output:
    research/results/processed/si_figures/
        basic_experiments/cmu20/{backend}/{variant}/summary.csv
        basic_experiments/cmu20/baselines/{method}/summary.csv
        basic_experiments/summaries/cmu20_ablation_4backend.csv
        advanced_experiments/chemical_slip_interpretability/cmu20/slip_analysis.csv
        advanced_experiments/mace_force_field_sensitivity/.../ablation_summary.csv
        advanced_experiments/gpt54_multiseed_cmu20/{seed}/ablation_summary.csv
"""

import csv
import os
import shutil
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'research', 'results')
OUTPUT_DIR = os.path.join(RESULTS_DIR, 'processed', 'si_figures')

# Backend short→long mapping
BACKEND_SHORT_LONG = {
    'gpt':    'gpt54_mace_mp0_small',
    'gemini': 'gemini25pro_mace_mp0_small',
    'claude': 'claude_sonnet46_mace_mp0_small',
    'grok':   'grok4_mace_mp0_small',
}

# Multi-seed directories
SEEDS = ['seed43', 'seed44', 'seed45', 'seed46', 'seed47']


def ensure_output_dir(*parts):
    d = os.path.join(OUTPUT_DIR, *parts)
    os.makedirs(d, exist_ok=True)
    return d


def copy_csv(src, dst):
    """Copy CSV as-is."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return sum(1 for _ in open(dst)) - 1


def copy_csv_drop_cols(src, dst, drop_prefixes):
    """Copy CSV but drop columns whose names start with given prefixes."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'r') as f_in:
        reader = csv.DictReader(f_in)
        all_cols = reader.fieldnames
        keep_cols = [c for c in all_cols
                     if not any(c.startswith(p) for p in drop_prefixes)]
        rows = [{c: row[c] for c in keep_cols} for row in reader]

    with open(dst, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=keep_cols)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def process_backend_variants():
    """Copy per-backend/variant summary.csv files (drop metadata columns)."""
    n = 0
    for short_be, long_be in BACKEND_SHORT_LONG.items():
        for var in ['full', 'one_shot', 'no_slip', 'no_forbid', 'no_termination']:
            src = os.path.join(RESULTS_DIR, 'basic_experiments', 'cmu20',
                               long_be, var, 'summary.csv')
            dst = os.path.join(OUTPUT_DIR, 'basic_experiments', 'cmu20',
                               short_be, var, 'summary.csv')
            if not os.path.exists(src):
                print(f"  WARNING: missing {os.path.relpath(src, RESULTS_DIR)}")
                continue
            rows = copy_csv_drop_cols(src, dst, ['backend_key', 'backend', 'llm_model',
                                                  'force_field', 'calculator_backend',
                                                  'force_field_model', 'force_field_size'])
            n += rows
    print(f"  Backend variants: {n} rows across 20 files")


def process_baselines():
    """Copy baseline summary files."""
    baselines_sherry = {
        'random_n20': 'random_n20',
        'heuristic': 'heuristic',
        'adsorbagent_mace_mp0_small_gpt54': 'adsorbagent_gpt54_mace_mp0_small',
    }
    n = 0
    for short_name, long_name in baselines_sherry.items():
        src = os.path.join(RESULTS_DIR, 'basic_experiments', 'cmu20',
                           'baselines', long_name, 'summary.csv')
        dst = os.path.join(OUTPUT_DIR, 'basic_experiments', 'cmu20',
                           'baselines', short_name, 'summary.csv')
        rows = copy_csv(src, dst)
        n += rows
    print(f"  Baselines: {n} rows across 3 files")


def process_slip_analysis():
    """Rename slip_analysis.csv columns from long to short backend names."""
    src = os.path.join(RESULTS_DIR, 'advanced_experiments',
                       'ablation_and_chemical_slip_diagnostics',
                       'chemical_slip_interpretability', 'cmu20',
                       'slip_analysis.csv')
    dst = os.path.join(OUTPUT_DIR, 'advanced_experiments',
                       'chemical_slip_interpretability', 'cmu20',
                       'slip_analysis.csv')
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    col_map = {}
    # slip_analysis.csv uses 'grok4' (not 'grok') for grok short names
    slip_backend_map = {
        'gpt54_mace_mp0_small':      'gpt',
        'gemini25pro_mace_mp0_small': 'gemini',
        'claude_sonnet46_mace_mp0_small': 'claude',
        'grok4_mace_mp0_small':      'grok4',
    }
    for long_be, short_be in slip_backend_map.items():
        col_map[f'{long_be}_planned_site'] = f'{short_be}_planned_site'
        col_map[f'{long_be}_actual_site'] = f'{short_be}_actual_site'
        col_map[f'{long_be}_slip'] = f'{short_be}_slip'
        col_map[f'{long_be}_slip_type'] = f'{short_be}_slip_type'

    with open(src, 'r') as f:
        reader = csv.DictReader(f)
        new_cols = [col_map.get(c, c) for c in reader.fieldnames]
        rows = list(reader)

    with open(dst, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_cols)
        writer.writeheader()
        for row in rows:
            new_row = {col_map.get(k, k): v for k, v in row.items()}
            writer.writerow(new_row)

    print(f"  slip_analysis.csv: {len(rows)} rows, {len(col_map)} columns renamed")


def process_ablation_4backend():
    """Copy ablation_4backend.csv (already processed for Figure 3, reuse)."""
    src = os.path.join(RESULTS_DIR, 'processed', 'figure3', 'ablation_4backend.csv')
    dst = os.path.join(OUTPUT_DIR, 'basic_experiments', 'cmu20',
                       'summaries', 'ablation_4backend.csv')
    rows = copy_csv(src, dst)
    print(f"  ablation_4backend.csv: {rows} rows (reused from figure3)")


def process_multiseed():
    """Copy multi-seed data (summary.csv → ablation_summary.csv)."""
    n = 0
    for seed in SEEDS:
        src = os.path.join(RESULTS_DIR, 'advanced_experiments', 'reproducibility',
                           'cmu20_gpt54_mace_mp0_small_multiseed', seed, 'full',
                           'summary.csv')
        dst = os.path.join(OUTPUT_DIR, 'advanced_experiments',
                           'gpt54_multiseed_cmu20', f'{seed}_full',
                           'ablation_summary.csv')
        rows = copy_csv_drop_cols(src, dst, ['backend_key', 'backend', 'llm_model',
                                              'force_field', 'calculator_backend',
                                              'force_field_model', 'force_field_size',
                                              'variant', 'delta_vs_full'])
        n += rows
    print(f"  Multi-seed: {n} rows across {len(SEEDS)} seeds")


def process_mace_sensitivity():
    """Copy MACE sensitivity data (summary.csv → ablation_summary.csv)."""
    src = os.path.join(RESULTS_DIR, 'advanced_experiments',
                       'force_field_sensitivity',
                       'mace_mp0_large_vs_mace_mp0_small', 'cmu20',
                       'gpt54_mace_mp0_large', 'full', 'summary.csv')
    dst = os.path.join(OUTPUT_DIR, 'advanced_experiments',
                       'mace_force_field_sensitivity',
                       'cmu20_gpt_full_mace_mp0_large', 'ablation_summary.csv')
    rows = copy_csv_drop_cols(src, dst, ['backend_key', 'backend', 'llm_model',
                                          'force_field', 'calculator_backend',
                                          'force_field_model', 'force_field_size',
                                          'variant', 'delta_vs_full'])
    print(f"  MACE sensitivity: {rows} rows")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output: {OUTPUT_DIR}\n")

    print("=" * 50)
    print("Processing SI figure data...")
    print("=" * 50)

    process_backend_variants()
    process_baselines()
    process_slip_analysis()
    process_ablation_4backend()
    process_multiseed()
    process_mace_sensitivity()

    print("=" * 50)
    print("Done. All SI data prepared.")
    print(f"Notebooks should replace 'results_sherry' with 'results/processed/si_figures'.")


if __name__ == '__main__':
    main()
