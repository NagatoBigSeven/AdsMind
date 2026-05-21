#!/usr/bin/env python3
"""
Prepare Figure 3 data from results/ raw data.

Reads original data from research/results/ and writes processed versions to
research/results/processed/figure3/ with backend key names remapped from long
to short form, matching the format expected by figure3_panels_updated.ipynb.

Usage:
    python research/paper_plots/scripts/prepare_figure3_data.py

Output:
    research/results/processed/figure3/
        iteration_convergence.csv   (Panel a)
        method_comparison.csv       (Panel a — reference energies)
        slip_analysis.json          (Panel b)
        ablation_4backend.csv       (Panel c — heatmap)
"""

import csv
import json
import os
import sys

# --- Paths relative to AdsMind project root ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'research', 'results')
OUTPUT_DIR = os.path.join(RESULTS_DIR, 'processed', 'figure3')

# --- Backend key mapping: long (results/) → short (Sherry / notebook) ---
# NOTE: Sherry uses TWO different short names for Claude across files:
#   iteration_convergence.csv → 'anthropic_sonnet46'
#   slip_analysis.json        → 'anthropic_claude'
# The notebook already handles this per-panel. We must match Sherry per-file.

# Mapping for iteration_convergence.csv
ITER_CONV_MAP = {
    'gemini25pro_mace_mp0_small':      'gemini',
    'grok4_mace_mp0_small':            'grok4',
    'gpt54_mace_mp0_small':            'openai_gpt54',
    'claude_sonnet46_mace_mp0_small':  'anthropic_sonnet46',
}

# Mapping for slip_analysis.json (different Claude name!)
SLIP_MAP = {
    'gemini25pro_mace_mp0_small':      'gemini',
    'grok4_mace_mp0_small':            'grok4',
    'gpt54_mace_mp0_small':            'openai_gpt54',
    'claude_sonnet46_mace_mp0_small':  'anthropic_claude',
    # _n suffixes
    'gpt54_mace_mp0_small_n':          'openai_gpt54_n',
    'claude_sonnet46_mace_mp0_small_n': 'anthropic_claude_n',
}


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def process_iteration_convergence():
    """
    Read iteration_convergence.csv from results/, remap backend names,
    keep only Sherry-format columns.
    """
    src = os.path.join(
        RESULTS_DIR,
        'advanced_experiments', 'case_studies', 'iteration_convergence',
        'cmu20', 'all_backends', 'full', 'iteration_convergence.csv',
    )
    dst = os.path.join(OUTPUT_DIR, 'iteration_convergence.csv')

    rows = []
    with open(src, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_backend = row['backend']
            if old_backend not in ITER_CONV_MAP:
                print(f"  WARNING: unknown backend '{old_backend}' — skipping row")
                continue
            rows.append({
                'case_id': row['case_id'],
                'backend': ITER_CONV_MAP[old_backend],
                'iter_1': row['iter_1'],
                'iter_2': row['iter_2'],
                'iter_3': row['iter_3'],
                'iter_4': row['iter_4'],
                'iter_5': row['iter_5'],
                'final_best': row['final_best'],
            })

    with open(dst, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'case_id', 'backend', 'iter_1', 'iter_2', 'iter_3',
            'iter_4', 'iter_5', 'final_best',
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"  iteration_convergence.csv: {len(rows)} rows written")
    return True


def process_method_comparison():
    """
    Copy method_comparison.csv as-is — already compatible with notebook.
    """
    src = os.path.join(
        RESULTS_DIR,
        'basic_experiments', 'summaries', 'cmu20_method_comparison.csv',
    )
    dst = os.path.join(OUTPUT_DIR, 'method_comparison.csv')

    with open(src, 'r') as f_in, open(dst, 'w', newline='') as f_out:
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        for row in reader:
            writer.writerow(row)

    line_count = sum(1 for _ in open(dst)) - 1  # minus header
    print(f"  method_comparison.csv: {line_count} data rows copied as-is")
    return True


def remap_keys(obj):
    """Recursively remap backend keys using SLIP_MAP."""
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            new_key = SLIP_MAP.get(k, k)
            new[new_key] = remap_keys(v)
        return new
    elif isinstance(obj, list):
        return [remap_keys(item) for item in obj]
    else:
        return obj


def process_slip_analysis():
    """
    Read slip_analysis.json from results/, remap backend keys,
    strip backend_metadata section (not in Sherry's version).
    """
    src = os.path.join(
        RESULTS_DIR,
        'advanced_experiments', 'ablation_and_chemical_slip_diagnostics',
        'chemical_slip_interpretability', 'cmu20', 'slip_analysis.json',
    )
    dst = os.path.join(OUTPUT_DIR, 'slip_analysis.json')

    # Force UTF-8 (handles BOM) to avoid Windows default GBK decode errors.
    with open(src, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    # Remove backend_metadata (Sherry's version doesn't have it)
    data.pop('backend_metadata', None)

    # Remap all backend keys
    data = remap_keys(data)

    with open(dst, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Quick sanity check
    overall = data.get('overall_slip_rate', {})
    expected_keys = ['gemini', 'grok4', 'openai_gpt54', 'anthropic_claude']
    found = [k for k in expected_keys if k in overall]
    print(f"  slip_analysis.json: overall keys remapped ok ({len(found)}/4 short keys present)")
    return True


def process_ablation_4backend():
    """
    Read ablation_4backend.csv from results/, promote backend_key to backend
    (already short names), drop long-name columns and extra metadata.
    Uses results/ values as-is (including gemini, per HaoYue's decision).
    """
    src = os.path.join(
        RESULTS_DIR,
        'basic_experiments', 'summaries', 'cmu20_ablation_4backend.csv',
    )
    dst = os.path.join(OUTPUT_DIR, 'ablation_4backend.csv')

    # Sherry's output columns (in order)
    output_cols = [
        'case_id', 'backend', 'variant', 'best_energy_eV', 'success',
        'run_path', 'iterations', 'wasted_iterations', 'waste_ratio',
        'slip_count', 'dissociation_count', 'tokens_used',
    ]

    rows = []
    with open(src, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'case_id': row['case_id'],
                'backend': row['backend_key'],  # use short name from backend_key
                'variant': row['variant'],
                'best_energy_eV': row['best_energy_eV'],
                'success': row['success'],
                'run_path': row['run_path'],
                'iterations': row['iterations'],
                'wasted_iterations': row['wasted_iterations'],
                'waste_ratio': row['waste_ratio'],
                'slip_count': row['slip_count'],
                'dissociation_count': row['dissociation_count'],
                'tokens_used': row['tokens_used'],
            })

    with open(dst, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_cols)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ablation_4backend.csv: {len(rows)} rows written (backend_key→backend, results/ values)")
    return True


def run():
    ensure_output_dir()

    print("\nProcessing Figure 3 data sources...")
    print("-" * 50)

    ok = True
    ok &= process_iteration_convergence()
    ok &= process_method_comparison()
    ok &= process_slip_analysis()
    ok &= process_ablation_4backend()

    print("-" * 50)
    if ok:
        print("All 4 files processed successfully.")
    else:
        print("Some files failed (see above).")
        sys.exit(1)


if __name__ == '__main__':
    run()
