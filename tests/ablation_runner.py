"""
SCOPE — Ablation Study Runner
==============================
Single-variable ablation: varies one utility weight at a time while
holding all others at their baseline values.

Experiment design:
    N        = 5000 nodes
    Seeds    = 10 independent runs per configuration
    Baseline = {α=2.0, β=0.6, γ=1.0, δ=0.3}
    Sweeps   = vary each param independently across its range

Outputs:
    results/ablation_results.csv          — raw per-seed metrics
    results/ablation_summary.csv          — mean ± std across seeds
    results/figures/fig1_apl_vs_delta.pdf/png
    results/figures/fig2_clustering_vs_gamma.pdf/png
    results/figures/fig3_hops_vs_alpha.pdf/png
    results/figures/fig4_throughput_vs_delta.pdf/png

Usage:
    python -m tests.ablation_runner          # full run (takes ~30–60 min on M2 Pro)
    python -m tests.ablation_runner --quick  # N=500, 3 seeds (fast smoke test ~2 min)
"""

import argparse
import os
import sys
import time
import warnings
from itertools import product

import matplotlib
matplotlib.use('Agg')   # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from tqdm import tqdm

# ── ensure project root is on sys.path ───────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.simulation import run_simulation_parameterized
from src.config import (
    ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT,
    ITERATIONS, NUM_NODES, SEED,
)

# ── matplotlib style ──────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':       'sans-serif',
    'font.sans-serif':   ['DejaVu Sans'],
    'font.size':         11,
    'axes.titlesize':    13,
    'axes.labelsize':    12,
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'axes.grid':         True,
    'grid.alpha':        0.35,
    'grid.linewidth':    0.6,
    'lines.linewidth':   2.0,
    'lines.markersize':  7,
    'figure.dpi':        150,
    'savefig.dpi':       300,
    'savefig.bbox':      'tight',
})

# Colour palette — one per swept parameter
PARAM_COLORS = {
    'alpha': '#3A86FF',
    'beta':  '#FF6B6B',
    'gamma': '#06D6A0',
    'delta': '#FFB703',
}

# ── experiment configuration ─────────────────────────────────────────────────
BASELINE = {
    'alpha':    ALPHA,            # 2.0
    'beta':     BETA,             # 0.6
    'gamma':    GAMMA,            # 1.0
    'delta':    DELTA_WEIGHT,     # 0.3
    'bw_weight': BETWEENNESS_WEIGHT,
}

# Single-variable sweeps: vary each param while fixing the rest at baseline
SWEEPS = {
    'alpha': [0.5, 1.0, 2.0, 3.0, 4.0],   # baseline = 2.0
    'beta':  [0.1, 0.3, 0.6, 0.9, 1.2],   # baseline = 0.6
    'gamma': [0.2, 0.5, 1.0, 1.5, 2.0],   # baseline = 1.0
    'delta': [0.0, 0.1, 0.2, 0.3, 0.5],   # baseline = 0.3
}

FULL_SEEDS  = list(range(10))   # 10 seeds for full run
QUICK_SEEDS = [0, 1, 2]         # 3 seeds for quick smoke test


# ── single run wrapper ────────────────────────────────────────────────────────
def run_one(alpha, beta, gamma, delta, bw_weight, seed, num_nodes, iterations):
    """Run one simulation and return a flat metrics dict."""
    result = run_simulation_parameterized(
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        bw_weight=bw_weight,
        delta=delta,
        num_nodes=num_nodes,
        seed=seed,
        iterations=iterations,
        verbose=False,
    )
    return {
        'alpha':              alpha,
        'beta':               beta,
        'gamma':              gamma,
        'delta':              delta,
        'seed':               seed,
        'initial_apl':        result['initial_apl'],
        'final_apl':          result['final_apl'],
        'apl_reduction_pct':  result['apl_reduction_pct'],
        'initial_clustering': result['initial_clustering'],
        'final_clustering':   result['final_clustering'],
        'final_search_hops':  result['final_search_hops'],
        'search_success_pct': result['search_success_pct'],
        'avg_bw_hub':         result['avg_bw_hub'],
        'avg_bw_leaf':        result['avg_bw_leaf'],
        'bw_multiplier':      result['bw_multiplier'],
    }


# ── main ablation loop ────────────────────────────────────────────────────────
def run_ablation(num_nodes, seeds, iterations, out_dir, figures_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    all_rows = []

    # Count total runs for outer progress bar
    total_runs = sum(len(vals) for vals in SWEEPS.values()) * len(seeds)
    print(f"\n{'='*60}")
    print(f"  SCOPE Ablation Study")
    print(f"  N={num_nodes} | {len(seeds)} seeds | {iterations} iterations/run")
    print(f"  Total configurations: {total_runs}")
    print(f"{'='*60}\n")

    pbar = tqdm(total=total_runs, desc='Ablation progress', unit='run')
    t0 = time.time()

    for param_name, sweep_values in SWEEPS.items():
        print(f"\n── Sweeping {param_name} over {sweep_values} ──")
        for val in sweep_values:
            # Build param dict: baseline + override the swept param
            params = {**BASELINE, param_name: val}

            for seed in seeds:
                row = run_one(
                    alpha=params['alpha'],
                    beta=params['beta'],
                    gamma=params['gamma'],
                    delta=params['delta'],
                    bw_weight=params['bw_weight'],
                    seed=seed,
                    num_nodes=num_nodes,
                    iterations=iterations,
                )
                row['swept_param']  = param_name
                row['swept_value']  = val
                all_rows.append(row)
                pbar.update(1)

    pbar.close()
    elapsed = time.time() - t0
    print(f"\nAll runs complete in {elapsed/60:.1f} min")

    df = pd.DataFrame(all_rows)
    raw_csv = os.path.join(out_dir, 'ablation_results.csv')
    df.to_csv(raw_csv, index=False)
    print(f"Raw results saved → {raw_csv}")

    # ── summary: mean ± std across seeds ─────────────────────────────────────
    metric_cols = [
        'final_apl', 'apl_reduction_pct',
        'final_clustering', 'final_search_hops',
        'search_success_pct', 'avg_bw_hub', 'bw_multiplier',
    ]
    summary_rows = []
    for (param_name, val), grp in df.groupby(['swept_param', 'swept_value']):
        row = {'swept_param': param_name, 'swept_value': val}
        for col in metric_cols:
            row[f'{col}_mean'] = grp[col].mean()
            row[f'{col}_std']  = grp[col].std()
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(out_dir, 'ablation_summary.csv')
    summary.to_csv(summary_csv, index=False)
    print(f"Summary saved → {summary_csv}")

    return df, summary


# ── figure generation ─────────────────────────────────────────────────────────
def save_fig(fig, figures_dir, stem):
    for ext in ('pdf', 'png'):
        path = os.path.join(figures_dir, f'{stem}.{ext}')
        fig.savefig(path)
        print(f"  Saved {path}")
    plt.close(fig)


def plot_apl_vs_delta(summary, figures_dir):
    """Fig 1 — APL reduction (%) as δ varies. Shows Proof-of-Throughput effect."""
    df_d = summary[summary['swept_param'] == 'delta'].sort_values('swept_value')
    if df_d.empty:
        print("  [skip] No delta data")
        return

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x   = df_d['swept_value'].values
    y   = df_d['apl_reduction_pct_mean'].values
    err = df_d['apl_reduction_pct_std'].values

    ax.fill_between(x, y - err, y + err, alpha=0.18, color=PARAM_COLORS['delta'])
    ax.plot(x, y, 'o-', color=PARAM_COLORS['delta'], label='APL Reduction (%)')
    ax.axvline(BASELINE['delta'], ls='--', lw=1.2, color='#555', label=f'Baseline δ={BASELINE["delta"]}')

    ax.set_xlabel('δ (Proof-of-Throughput weight)')
    ax.set_ylabel('APL Reduction vs. Random Graph (%)')
    ax.set_title('Fig 1 — Effect of δ on Routing Efficiency\n(avg path length reduction over 10 seeds)')
    ax.legend(framealpha=0.5)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%'))

    fig.tight_layout()
    save_fig(fig, figures_dir, 'fig1_apl_vs_delta')


def plot_clustering_vs_gamma(summary, figures_dir):
    """Fig 2 — Final clustering coefficient as γ varies."""
    df_g = summary[summary['swept_param'] == 'gamma'].sort_values('swept_value')
    if df_g.empty:
        print("  [skip] No gamma data")
        return

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x   = df_g['swept_value'].values
    y   = df_g['final_clustering_mean'].values
    err = df_g['final_clustering_std'].values

    ax.fill_between(x, y - err, y + err, alpha=0.18, color=PARAM_COLORS['gamma'])
    ax.plot(x, y, 's-', color=PARAM_COLORS['gamma'], label='Final Clustering Coeff.')
    ax.axvline(BASELINE['gamma'], ls='--', lw=1.2, color='#555', label=f'Baseline γ={BASELINE["gamma"]}')

    ax.set_xlabel('γ (Social Similarity weight)')
    ax.set_ylabel('Final Average Clustering Coefficient')
    ax.set_title('Fig 2 — Effect of γ on Emergent Social Clustering\n(10 seeds; shaded = ±1 std dev)')
    ax.legend(framealpha=0.5)

    fig.tight_layout()
    save_fig(fig, figures_dir, 'fig2_clustering_vs_gamma')


def plot_hops_vs_alpha(summary, figures_dir):
    """Fig 3 — Final search hops vs α (centrality incentive strength)."""
    df_a = summary[summary['swept_param'] == 'alpha'].sort_values('swept_value')
    if df_a.empty:
        print("  [skip] No alpha data")
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Left: hop count
    x   = df_a['swept_value'].values
    y   = df_a['final_search_hops_mean'].values
    err = df_a['final_search_hops_std'].values
    axes[0].fill_between(x, y - err, y + err, alpha=0.18, color=PARAM_COLORS['alpha'])
    axes[0].plot(x, y, '^-', color=PARAM_COLORS['alpha'])
    axes[0].axvline(BASELINE['alpha'], ls='--', lw=1.2, color='#555', label=f'Baseline α={BASELINE["alpha"]}')
    axes[0].set_xlabel('α (Centrality Benefit weight)')
    axes[0].set_ylabel('Avg Search Hops (lower = better)')
    axes[0].set_title('Search Hop Count vs α')
    axes[0].legend(framealpha=0.5)

    # Right: success rate
    y2   = df_a['search_success_pct_mean'].values
    err2 = df_a['search_success_pct_std'].values
    axes[1].fill_between(x, y2 - err2, y2 + err2, alpha=0.18, color=PARAM_COLORS['alpha'])
    axes[1].plot(x, y2, 'o-', color=PARAM_COLORS['alpha'])
    axes[1].axvline(BASELINE['alpha'], ls='--', lw=1.2, color='#555')
    axes[1].set_xlabel('α (Centrality Benefit weight)')
    axes[1].set_ylabel('Search Success Rate (%)')
    axes[1].set_title('Search Success Rate vs α')
    axes[1].yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%'))

    fig.suptitle('Fig 3 — Effect of α on Gradient-Ascent Search Performance\n(10 seeds; shaded = ±1 std dev)',
                 fontsize=13, y=1.02)
    fig.tight_layout()
    save_fig(fig, figures_dir, 'fig3_hops_vs_alpha')


def plot_throughput_vs_delta(summary, figures_dir):
    """Fig 4 — Hub/leaf bandwidth multiplier vs δ. Shows Proof-of-Throughput incentive strength."""
    df_d = summary[summary['swept_param'] == 'delta'].sort_values('swept_value')
    if df_d.empty:
        print("  [skip] No delta data")
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    x = df_d['swept_value'].values

    # Left: absolute bandwidth (hub vs leaf)
    y_hub  = df_d['avg_bw_hub_mean'].values
    axes[0].plot(x, y_hub, 'D-', color='#3A86FF', label='Hub nodes (deg > 10)')
    axes[0].set_xlabel('δ (Proof-of-Throughput weight)')
    axes[0].set_ylabel('Avg Bandwidth (Mbps)')
    axes[0].set_title('Bandwidth by Node Tier vs δ')
    axes[0].legend(framealpha=0.5)
    axes[0].axvline(BASELINE['delta'], ls='--', lw=1.2, color='#555')

    # Right: bandwidth multiplier (hub / leaf ratio)
    y_mult = df_d['bw_multiplier_mean'].values
    err    = df_d['bw_multiplier_std'].values
    axes[1].fill_between(x, y_mult - err, y_mult + err, alpha=0.18, color=PARAM_COLORS['delta'])
    axes[1].plot(x, y_mult, 'o-', color=PARAM_COLORS['delta'], label='Hub/Leaf BW ratio')
    axes[1].axvline(BASELINE['delta'], ls='--', lw=1.2, color='#555', label=f'Baseline δ={BASELINE["delta"]}')
    axes[1].axhline(1.0, ls=':', lw=1, color='#888', label='No incentive (ratio=1)')
    axes[1].set_xlabel('δ (Proof-of-Throughput weight)')
    axes[1].set_ylabel('Hub / Leaf Bandwidth Multiplier')
    axes[1].set_title('Incentive Multiplier vs δ')
    axes[1].legend(framealpha=0.5)

    fig.suptitle('Fig 4 — Proof-of-Throughput: Effect of δ on Bandwidth Incentive\n(10 seeds; shaded = ±1 std dev)',
                 fontsize=13, y=1.02)
    fig.tight_layout()
    save_fig(fig, figures_dir, 'fig4_throughput_vs_delta')


def generate_all_figures(summary, figures_dir):
    print(f"\nGenerating publication figures → {figures_dir}/")
    plot_apl_vs_delta(summary, figures_dir)
    plot_clustering_vs_gamma(summary, figures_dir)
    plot_hops_vs_alpha(summary, figures_dir)
    plot_throughput_vs_delta(summary, figures_dir)
    print("All figures saved (PDF + PNG)")


def print_summary_table(summary):
    """Print a readable summary table to stdout for copy-paste into the paper."""
    print("\n" + "=" * 70)
    print("  ABLATION STUDY — SUMMARY (mean ± std across seeds)")
    print("=" * 70)
    for param_name in ['alpha', 'beta', 'gamma', 'delta']:
        df_p = summary[summary['swept_param'] == param_name].sort_values('swept_value')
        if df_p.empty:
            continue
        print(f"\n  Swept parameter: {param_name}")
        print(f"  {'Value':>8}  {'Final APL':>12}  {'APL Δ%':>10}  {'CC':>10}  {'Hops':>8}  {'Success%':>10}  {'BW×':>6}")
        print(f"  {'-'*8}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*10}  {'-'*6}")
        for _, r in df_p.iterrows():
            marker = ' ◄' if abs(r['swept_value'] - BASELINE[param_name]) < 1e-9 else ''
            print(
                f"  {r['swept_value']:>8.2f}  "
                f"{r['final_apl_mean']:>6.4f}±{r['final_apl_std']:.4f}  "
                f"{r['apl_reduction_pct_mean']:>+8.2f}%  "
                f"{r['final_clustering_mean']:>8.4f}  "
                f"{r['final_search_hops_mean']:>8.2f}  "
                f"{r['search_success_pct_mean']:>8.1f}%  "
                f"{r['bw_multiplier_mean']:>5.2f}×"
                f"{marker}"
            )
    print()


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SCOPE Ablation Study Runner')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: N=500, 3 seeds (~2 min smoke test)')
    parser.add_argument('--seeds', type=int, default=None,
                        help='Override number of seeds (default: 10 full / 3 quick)')
    parser.add_argument('--nodes', type=int, default=None,
                        help='Override number of nodes (default: 5000 full / 500 quick)')
    parser.add_argument('--iterations', type=int, default=ITERATIONS,
                        help=f'Sim iterations per run (default: {ITERATIONS})')
    parser.add_argument('--out-dir', default='results',
                        help='Output directory for CSVs (default: results/)')
    parser.add_argument('--fig-dir', default='results/figures',
                        help='Output directory for figures (default: results/figures/)')
    args = parser.parse_args()

    if args.quick:
        num_nodes  = args.nodes      or 500
        seeds      = QUICK_SEEDS[:args.seeds] if args.seeds else QUICK_SEEDS
        iterations = 20 if not args.iterations or args.iterations == ITERATIONS else args.iterations
        print(f"[QUICK MODE] N={num_nodes}, {len(seeds)} seeds, {iterations} iterations")
    else:
        num_nodes  = args.nodes or 5000
        seeds      = list(range(args.seeds)) if args.seeds else FULL_SEEDS
        iterations = args.iterations

    # Warm up Numba JIT before timing (first call compiles the function)
    print("Warming up Numba JIT compiler…")
    _ = run_simulation_parameterized(num_nodes=50, seed=0, iterations=3, verbose=False)
    print("JIT warm-up complete.\n")

    df_raw, df_summary = run_ablation(
        num_nodes=num_nodes,
        seeds=seeds,
        iterations=iterations,
        out_dir=args.out_dir,
        figures_dir=args.fig_dir,
    )

    generate_all_figures(df_summary, args.fig_dir)
    print_summary_table(df_summary)
    print(f"\nDone. Results in {args.out_dir}/\n")
