"""
SCOPE — Core-Periphery Emergence Monte Carlo Validation
=========================================================
Task 2.3: Generate quantitative core-periphery emergence empirical data
across 20 independent Monte Carlo seeds.

Author: Samarth Dave (Member 2)

This script runs independent simulations and extracts:
    - Assortativity coefficient r (mean ± std)
    - Core size |C| as fraction of total network
    - Core-periphery fit score (Borgatti-Everett ρ)
    - Emergence frequency (% of seeds where ρ > 0.15 and |C| > 0)

Outputs:
    results/core_periphery_results.csv   — raw per-seed metrics
    results/core_periphery_summary.csv   — aggregated statistics

Usage:
    python -m tests.core_periphery_runner            # full run (20 seeds)
    python -m tests.core_periphery_runner --quick    # quick test (5 seeds)
"""

import argparse
import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from tqdm import tqdm

# ── ensure project root is on sys.path ────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.simulation import run_simulation_parameterized
from src.config import (
    ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT,
    ITERATIONS, NUM_NODES,
)

# Default experiment parameters
DEFAULT_SEEDS = 20
QUICK_SEEDS   = 5
CP_FIT_THRESHOLD = 0.15   # ρ threshold for "stable core-periphery emergence"


def run_core_periphery_monte_carlo(num_nodes, seeds, iterations, out_dir):
    """Run independent simulations and collect CP emergence metrics."""
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"  Core-Periphery Emergence Monte Carlo Validation")
    print(f"  N={num_nodes} | {len(seeds)} seeds | {iterations} iterations/run")
    print(f"  CP emergence threshold: ρ > {CP_FIT_THRESHOLD}")
    print(f"{'=' * 60}\n")

    rows = []
    t0 = time.time()

    for seed in tqdm(seeds, desc='CP Monte Carlo', unit='seed'):
        result = run_simulation_parameterized(
            alpha=ALPHA,
            beta=BETA,
            gamma=GAMMA,
            bw_weight=BETWEENNESS_WEIGHT,
            delta=DELTA_WEIGHT,
            num_nodes=num_nodes,
            seed=seed,
            iterations=iterations,
            verbose=False,
        )

        rows.append({
            'seed':               seed,
            'num_nodes':          num_nodes,
            'iterations':         iterations,
            'core_size':          result['core_size'],
            'core_fraction':      result['core_fraction'],
            'assortativity':      result['assortativity'],
            'cp_fit_score':       result['cp_fit_score'],
            'final_apl':          result['final_apl'],
            'final_clustering':   result['final_clustering'],
            'apl_reduction_pct':  result['apl_reduction_pct'],
            'final_search_hops':  result['final_search_hops'],
            'search_success_pct': result['search_success_pct'],
            'bw_multiplier':      result['bw_multiplier'],
            # Flag: does this seed show stable CP emergence?
            'cp_emerged':         (result['cp_fit_score'] > CP_FIT_THRESHOLD and result['core_size'] > 0),
        })

    elapsed = time.time() - t0
    print(f"\nAll seeds complete in {elapsed / 60:.1f} min")

    df = pd.DataFrame(rows)
    raw_csv = os.path.join(out_dir, 'core_periphery_results.csv')
    df.to_csv(raw_csv, index=False)
    print(f"Raw results saved -> {raw_csv}")

    # ── Aggregate summary ──
    n_total = len(df)
    n_emerged = df['cp_emerged'].sum()
    emergence_freq = n_emerged / n_total * 100 if n_total > 0 else 0.0

    summary = {
        'num_seeds':                     n_total,
        'num_nodes':                     num_nodes,
        'iterations':                    iterations,
        'core_size_mean':                df['core_size'].mean(),
        'core_size_std':                 df['core_size'].std(),
        'core_fraction_mean':            df['core_fraction'].mean(),
        'core_fraction_std':             df['core_fraction'].std(),
        'assortativity_mean':            df['assortativity'].mean(),
        'assortativity_std':             df['assortativity'].std(),
        'cp_fit_score_mean':             df['cp_fit_score'].mean(),
        'cp_fit_score_std':              df['cp_fit_score'].std(),
        'emergence_frequency_pct':       emergence_freq,
        'final_apl_mean':                df['final_apl'].mean(),
        'final_apl_std':                 df['final_apl'].std(),
        'final_clustering_mean':         df['final_clustering'].mean(),
        'final_clustering_std':          df['final_clustering'].std(),
        'apl_reduction_pct_mean':        df['apl_reduction_pct'].mean(),
        'apl_reduction_pct_std':         df['apl_reduction_pct'].std(),
    }

    summary_df = pd.DataFrame([summary])
    summary_csv = os.path.join(out_dir, 'core_periphery_summary.csv')
    summary_df.to_csv(summary_csv, index=False)
    print(f"Summary saved -> {summary_csv}")

    # ── Print readable table ──
    print(f"\n{'=' * 60}")
    print(f"  CORE-PERIPHERY EMERGENCE SUMMARY")
    print(f"  {n_total} independent seeds, N={num_nodes}")
    print(f"{'=' * 60}")
    print(f"  Core Size |C|       : {summary['core_size_mean']:.2f} ± {summary['core_size_std']:.2f} nodes")
    print(f"  Core Fraction       : {summary['core_fraction_mean']*100:.2f}% ± {summary['core_fraction_std']*100:.2f}%")
    print(f"  Assortativity r     : {summary['assortativity_mean']:.4f} ± {summary['assortativity_std']:.4f}")
    print(f"  CP Fit Score ρ      : {summary['cp_fit_score_mean']:.4f} ± {summary['cp_fit_score_std']:.4f}")
    print(f"  Emergence Frequency : {emergence_freq:.1f}% ({n_emerged}/{n_total} seeds with ρ > {CP_FIT_THRESHOLD})")
    print(f"  Final APL           : {summary['final_apl_mean']:.4f} ± {summary['final_apl_std']:.4f}")
    print(f"  Final Clustering    : {summary['final_clustering_mean']:.4f} ± {summary['final_clustering_std']:.4f}")
    print(f"  APL Reduction       : {summary['apl_reduction_pct_mean']:.2f}% ± {summary['apl_reduction_pct_std']:.2f}%")
    print()

    return df, summary_df


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SCOPE Core-Periphery Monte Carlo Runner')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: 5 seeds')
    parser.add_argument('--seeds', type=int, default=None,
                        help='Override number of seeds (default: 20)')
    parser.add_argument('--nodes', type=int, default=None,
                        help='Override number of nodes')
    parser.add_argument('--iterations', type=int, default=ITERATIONS,
                        help=f'Sim iterations per run (default: {ITERATIONS})')
    parser.add_argument('--out-dir', default='results',
                        help='Output directory for CSVs')
    args = parser.parse_args()

    if args.quick:
        num_nodes = args.nodes or 500
        num_seeds = args.seeds or QUICK_SEEDS
        iterations = 20
        print(f"[QUICK MODE] N={num_nodes}, {num_seeds} seeds, {iterations} iterations")
    else:
        num_nodes = args.nodes or 500
        num_seeds = args.seeds or DEFAULT_SEEDS
        iterations = args.iterations

    seeds = list(range(num_seeds))

    # Warm up Numba
    print("Warming up Numba JIT compiler…")
    _ = run_simulation_parameterized(num_nodes=50, seed=0, iterations=3, verbose=False)
    print("JIT warm-up complete.\n")

    df_raw, df_summary = run_core_periphery_monte_carlo(
        num_nodes=num_nodes,
        seeds=seeds,
        iterations=iterations,
        out_dir=args.out_dir,
    )

    print(f"Done. Results in {args.out_dir}/\n")
