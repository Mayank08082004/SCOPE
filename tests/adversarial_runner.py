"""
SCOPE — Adversarial Resilience Evaluation Runner
==================================================
Task 2.1 & 2.2: Multi-strategy adversarial defector sweep with detection
accuracy metrics (FPR, FNR, Time-to-Isolation).

Author: Samarth Dave (Member 2)

Experiment design:
    Attacker types:  naive_liar, intermittent_dropper, colluding_sybil, sleeper
    Defector ratios: 5%, 10%, 20%, 30%
    Seeds:           10 independent runs per configuration (default)
    N:               500 nodes (default), configurable

Outputs:
    results/adversarial_results.csv          — raw per-seed metrics
    results/adversarial_summary.csv          — mean ± std across seeds
    results/figures/fig5_adversarial_resilience.pdf/png

Usage:
    python -m tests.adversarial_runner              # full run
    python -m tests.adversarial_runner --quick      # quick smoke test (N=200, 3 seeds)
"""

import argparse
import os
import sys
import time
import warnings

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from tqdm import tqdm

# ── ensure project root is on sys.path ────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import random
import networkx as nx

from src.simulation import (
    initialize_graph, compute_metrics, compute_core_periphery_metrics,
    test_routing_performance,
)
from src.config import (
    ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT,
    ITERATIONS, INITIAL_DEGREE, QUERY_TTL, NUM_SEARCH_QUERIES,
    REWIRING_PROB,
)
from src.agent import (
    PeerAgent, NaiveLiarAgent, IntermittentDropperAgent,
    ColludingSybilAgent, SleeperAgent, create_adversarial_agent,
)

# ── matplotlib style ──────────────────────────────────────────────────────
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

# Colour palette — one per attacker type
ATTACKER_COLORS = {
    'naive_liar':           '#FF6B6B',
    'intermittent_dropper': '#FFB703',
    'colluding_sybil':      '#8338EC',
    'sleeper':              '#06D6A0',
}

ATTACKER_LABELS = {
    'naive_liar':           'Type 1: Naive Liar',
    'intermittent_dropper': 'Type 2: Intermittent Dropper',
    'colluding_sybil':      'Type 3: Colluding Sybil',
    'sleeper':              'Type 4: Sleeper Agent',
}

# Experiment parameters
DEFECTOR_RATIOS = [0.05, 0.10, 0.20, 0.30]
ATTACKER_TYPES  = ['naive_liar', 'intermittent_dropper', 'colluding_sybil', 'sleeper']
FULL_SEEDS      = list(range(10))
QUICK_SEEDS     = [0, 1, 2]


def run_adversarial_simulation(
    attacker_type='naive_liar',
    defector_ratio=0.10,
    num_nodes=500,
    seed=42,
    iterations=50,
    alpha=ALPHA,
    beta=BETA,
    gamma=GAMMA,
    bw_weight=BETWEENNESS_WEIGHT,
    delta=DELTA_WEIGHT,
    rewiring_prob=REWIRING_PROB,
    num_queries=50,
    ttl=QUERY_TTL,
    verbose=False,
):
    """
    Run a single adversarial simulation with a specific attacker type and ratio.

    Returns a dict of scalar metrics including FPR, FNR, time-to-isolation,
    search performance, and core-periphery metrics.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Reset sybil clique for fresh experiment
    ColludingSybilAgent.reset_clique()

    G = initialize_graph(num_nodes=num_nodes, initial_degree=INITIAL_DEGREE, seed=seed)

    agents = {}
    malicious_ids = set()
    honest_ids = set()

    nodes = list(G.nodes())
    num_defectors = int(len(nodes) * defector_ratio)
    defector_nodes = set(random.sample(nodes, num_defectors))

    for node in nodes:
        if node in defector_nodes:
            agent = create_adversarial_agent(attacker_type, node, G)
            agents[node] = agent
            G.nodes[node]['is_defector'] = True
            malicious_ids.add(node)
        else:
            agents[node] = PeerAgent(node, G, is_defector=False)
            G.nodes[node]['is_defector'] = False
            honest_ids.add(node)

    # For colluding sybils, create internal edges between sybil nodes
    if attacker_type == 'colluding_sybil':
        sybil_list = list(defector_nodes)
        for i in range(len(sybil_list)):
            for j in range(i + 1, min(i + 4, len(sybil_list))):
                if not G.has_edge(sybil_list[i], sybil_list[j]):
                    G.add_edge(sybil_list[i], sybil_list[j])

    # Initial metrics
    initial_apl, initial_cc = compute_metrics(G)
    initial_hops, initial_success = test_routing_performance(
        G, agents, num_queries=num_queries, ttl=ttl
    )

    # Track degree history for defectors (for time-to-isolation)
    defector_degree_history = []  # list of {step: mean_defector_degree}
    isolation_step = None  # step at which mean defector degree reaches 0

    # Track honest node pruning (for FPR)
    initial_honest_edges = {}
    for nid in honest_ids:
        if G.has_node(nid):
            initial_honest_edges[nid] = set(G.neighbors(nid))

    # Evolution loop
    itr = range(iterations)
    if verbose:
        itr = tqdm(itr, desc=f"{attacker_type} r={defector_ratio} s={seed}", leave=False)

    for step in itr:
        # Betweenness centrality update
        k_bc = max(10, min(20, num_nodes // 250))
        bc = nx.betweenness_centrality(G, k=k_bc)
        max_bc = max(bc.values()) if bc else 0.0
        if max_bc > 0:
            bc = {nid: val / max_bc for nid, val in bc.items()}
        nx.set_node_attributes(G, bc, 'betweenness')

        # OODA loop
        active = random.sample(list(G.nodes()), int(len(G.nodes()) * rewiring_prob))
        for node_id in active:
            if node_id not in agents:
                continue
            agent = agents[node_id]
            _, drop, add, new_mem = agent.decide(
                alpha=alpha, beta=beta, gamma=gamma,
                bw_weight=bw_weight, delta=delta,
            )
            agent.memory = new_mem
            if drop and G.has_edge(node_id, drop):
                G.remove_edge(node_id, drop)
            if add:
                G.add_edge(node_id, add)

        # Track defector degree
        alive_defectors = [nid for nid in malicious_ids if G.has_node(nid)]
        if alive_defectors:
            mean_def_degree = np.mean([G.degree(nid) for nid in alive_defectors])
        else:
            mean_def_degree = 0.0
        defector_degree_history.append(mean_def_degree)

        # Check if defectors are isolated
        if isolation_step is None and mean_def_degree < 0.5:
            isolation_step = step + 1

    # ── Post-simulation metrics ──
    final_apl, final_cc = compute_metrics(G)
    final_hops, final_success = test_routing_performance(
        G, agents, num_queries=num_queries, ttl=ttl
    )
    cp_metrics = compute_core_periphery_metrics(G)

    # ── Detection accuracy metrics ──

    # False Positive Rate: honest nodes that lost ALL connections (pruned by the overlay)
    honest_pruned = 0
    total_honest = len(honest_ids)
    for nid in honest_ids:
        if G.has_node(nid):
            if G.degree(nid) == 0:
                honest_pruned += 1
        else:
            # node was removed entirely
            honest_pruned += 1
    fpr = honest_pruned / total_honest if total_honest > 0 else 0.0

    # False Negative Rate: malicious nodes that are still in core (degree > 0)
    malicious_retained = 0
    total_malicious = len(malicious_ids)
    for nid in malicious_ids:
        if G.has_node(nid) and G.degree(nid) > 0:
            malicious_retained += 1
    fnr = malicious_retained / total_malicious if total_malicious > 0 else 0.0

    # Time-to-Isolation: step at which mean defector degree drops below 0.5
    # If never isolated, report total iterations
    time_to_isolation = isolation_step if isolation_step is not None else iterations

    # Bandwidth stats
    bws = [(G.degree(nid), agent.calculate_bandwidth()) for nid, agent in agents.items() if G.has_node(nid)]
    hub_bws = [bw for deg, bw in bws if deg > 10]
    leaf_bws = [bw for deg, bw in bws if deg <= 3]
    avg_hub = float(np.mean(hub_bws)) if hub_bws else 0.0
    avg_leaf = float(np.mean(leaf_bws)) if leaf_bws else 0.0
    bw_mult = avg_hub / avg_leaf if avg_leaf > 0 else 0.0

    hop_reduction = (initial_hops - final_hops) / initial_hops * 100 if initial_hops > 0 else 0.0

    return {
        'attacker_type':            attacker_type,
        'defector_ratio':           defector_ratio,
        'seed':                     seed,
        'num_nodes':                num_nodes,
        'num_defectors':            num_defectors,
        # Search metrics
        'initial_search_hops':      initial_hops,
        'final_search_hops':        final_hops,
        'search_hop_reduction_pct': hop_reduction,
        'initial_search_success':   initial_success,
        'final_search_success':     final_success,
        # Network structure
        'initial_apl':              initial_apl,
        'final_apl':                final_apl,
        'initial_clustering':       initial_cc,
        'final_clustering':         final_cc,
        'apl_reduction_pct':        (initial_apl - final_apl) / initial_apl * 100 if initial_apl > 0 else 0.0,
        # Detection accuracy (Task 2.2)
        'fpr':                      round(fpr, 6),
        'fnr':                      round(fnr, 6),
        'time_to_isolation':        time_to_isolation,
        # Bandwidth
        'avg_bw_hub':               avg_hub,
        'avg_bw_leaf':              avg_leaf,
        'bw_multiplier':            bw_mult,
        # Core-periphery
        'core_size':                cp_metrics['core_size'],
        'core_fraction':            cp_metrics['core_fraction'],
        'assortativity':            cp_metrics['assortativity'],
        'cp_fit_score':             cp_metrics['cp_fit_score'],
    }


# ── Main sweep ────────────────────────────────────────────────────────────
def run_adversarial_sweep(num_nodes, seeds, iterations, out_dir, figures_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    total_runs = len(ATTACKER_TYPES) * len(DEFECTOR_RATIOS) * len(seeds)
    print(f"\n{'=' * 60}")
    print(f"  SCOPE Adversarial Resilience Evaluation")
    print(f"  N={num_nodes} | {len(seeds)} seeds | {iterations} iterations/run")
    print(f"  Attacker types: {len(ATTACKER_TYPES)} | Ratios: {DEFECTOR_RATIOS}")
    print(f"  Total configurations: {total_runs}")
    print(f"{'=' * 60}\n")

    all_rows = []
    pbar = tqdm(total=total_runs, desc='Adversarial sweep', unit='run')
    t0 = time.time()

    for atype in ATTACKER_TYPES:
        print(f"\n-- Attacker: {ATTACKER_LABELS[atype]} --")
        for ratio in DEFECTOR_RATIOS:
            for seed in seeds:
                row = run_adversarial_simulation(
                    attacker_type=atype,
                    defector_ratio=ratio,
                    num_nodes=num_nodes,
                    seed=seed,
                    iterations=iterations,
                    verbose=False,
                )
                all_rows.append(row)
                pbar.update(1)

    pbar.close()
    elapsed = time.time() - t0
    print(f"\nAll adversarial runs complete in {elapsed / 60:.1f} min")

    df = pd.DataFrame(all_rows)
    raw_csv = os.path.join(out_dir, 'adversarial_results.csv')
    df.to_csv(raw_csv, index=False)
    print(f"Raw results saved -> {raw_csv}")

    # ── Summary ──
    metric_cols = [
        'final_search_hops', 'search_hop_reduction_pct', 'final_search_success',
        'final_apl', 'apl_reduction_pct', 'final_clustering',
        'fpr', 'fnr', 'time_to_isolation',
        'avg_bw_hub', 'bw_multiplier',
        'core_size', 'core_fraction', 'assortativity', 'cp_fit_score',
    ]
    summary_rows = []
    for (atype, ratio), grp in df.groupby(['attacker_type', 'defector_ratio']):
        row = {'attacker_type': atype, 'defector_ratio': ratio}
        for col in metric_cols:
            row[f'{col}_mean'] = grp[col].mean()
            row[f'{col}_std'] = grp[col].std()
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(out_dir, 'adversarial_summary.csv')
    summary.to_csv(summary_csv, index=False)
    print(f"Summary saved -> {summary_csv}")

    return df, summary


# ── Figure generation ─────────────────────────────────────────────────────
def save_fig(fig, figures_dir, stem):
    for ext in ('pdf', 'png'):
        path = os.path.join(figures_dir, f'{stem}.{ext}')
        fig.savefig(path)
        print(f"  Saved {path}")
    plt.close(fig)


def plot_adversarial_resilience(summary, figures_dir):
    """
    Fig 5 — Adversarial Resilience: 2×2 grid showing
    (a) FNR vs defector ratio, (b) FPR vs defector ratio,
    (c) Time-to-Isolation vs defector ratio, (d) Search success vs defector ratio
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    # Panel (a): FNR
    ax = axes[0, 0]
    for atype in ATTACKER_TYPES:
        df_t = summary[summary['attacker_type'] == atype].sort_values('defector_ratio')
        if df_t.empty:
            continue
        x = df_t['defector_ratio'].values * 100
        y = df_t['fnr_mean'].values * 100
        err = df_t['fnr_std'].values * 100
        ax.fill_between(x, y - err, y + err, alpha=0.15, color=ATTACKER_COLORS[atype])
        ax.plot(x, y, 'o-', color=ATTACKER_COLORS[atype], label=ATTACKER_LABELS[atype])
    ax.set_xlabel('Defector Ratio (%)')
    ax.set_ylabel('False Negative Rate (%)')
    ax.set_title('(a) Malicious Nodes Surviving Pruning')
    ax.legend(fontsize=8, framealpha=0.5)

    # Panel (b): FPR
    ax = axes[0, 1]
    for atype in ATTACKER_TYPES:
        df_t = summary[summary['attacker_type'] == atype].sort_values('defector_ratio')
        if df_t.empty:
            continue
        x = df_t['defector_ratio'].values * 100
        y = df_t['fpr_mean'].values * 100
        err = df_t['fpr_std'].values * 100
        ax.fill_between(x, y - err, y + err, alpha=0.15, color=ATTACKER_COLORS[atype])
        ax.plot(x, y, 's-', color=ATTACKER_COLORS[atype], label=ATTACKER_LABELS[atype])
    ax.set_xlabel('Defector Ratio (%)')
    ax.set_ylabel('False Positive Rate (%)')
    ax.set_title('(b) Honest Nodes Incorrectly Pruned')
    ax.legend(fontsize=8, framealpha=0.5)

    # Panel (c): Time-to-Isolation
    ax = axes[1, 0]
    for atype in ATTACKER_TYPES:
        df_t = summary[summary['attacker_type'] == atype].sort_values('defector_ratio')
        if df_t.empty:
            continue
        x = df_t['defector_ratio'].values * 100
        y = df_t['time_to_isolation_mean'].values
        err = df_t['time_to_isolation_std'].values
        ax.fill_between(x, y - err, y + err, alpha=0.15, color=ATTACKER_COLORS[atype])
        ax.plot(x, y, '^-', color=ATTACKER_COLORS[atype], label=ATTACKER_LABELS[atype])
    ax.set_xlabel('Defector Ratio (%)')
    ax.set_ylabel('OODA Iterations to Isolation')
    ax.set_title('(c) Time-to-Isolation of Defectors')
    ax.legend(fontsize=8, framealpha=0.5)

    # Panel (d): Search Success Rate
    ax = axes[1, 1]
    for atype in ATTACKER_TYPES:
        df_t = summary[summary['attacker_type'] == atype].sort_values('defector_ratio')
        if df_t.empty:
            continue
        x = df_t['defector_ratio'].values * 100
        y = df_t['final_search_success_mean'].values
        err = df_t['final_search_success_std'].values
        ax.fill_between(x, y - err, y + err, alpha=0.15, color=ATTACKER_COLORS[atype])
        ax.plot(x, y, 'D-', color=ATTACKER_COLORS[atype], label=ATTACKER_LABELS[atype])
    ax.set_xlabel('Defector Ratio (%)')
    ax.set_ylabel('Search Success Rate (%)')
    ax.set_title('(d) Search Resilience Under Attack')
    ax.legend(fontsize=8, framealpha=0.5)

    fig.suptitle('Fig 5 — SCOPE Adversarial Resilience: Multi-Strategy Evaluation\n'
                 f'(N nodes, shaded = ±1 std dev)',
                 fontsize=14, y=1.02)
    fig.tight_layout()
    save_fig(fig, figures_dir, 'fig5_adversarial_resilience')


def print_adversarial_summary(summary):
    """Print a readable adversarial summary table."""
    print("\n" + "=" * 80)
    print("  ADVERSARIAL RESILIENCE — SUMMARY (mean ± std across seeds)")
    print("=" * 80)
    for atype in ATTACKER_TYPES:
        df_t = summary[summary['attacker_type'] == atype].sort_values('defector_ratio')
        if df_t.empty:
            continue
        print(f"\n  {ATTACKER_LABELS[atype]}")
        print(f"  {'Ratio':>8}  {'FPR':>10}  {'FNR':>10}  {'T2I':>6}  {'Hops':>8}  {'Success%':>10}  {'APL':>8}")
        print(f"  {'-'*8}  {'-'*10}  {'-'*10}  {'-'*6}  {'-'*8}  {'-'*10}  {'-'*8}")
        for _, r in df_t.iterrows():
            print(
                f"  {r['defector_ratio']*100:>6.0f}%  "
                f"{r['fpr_mean']*100:>5.2f}±{r['fpr_std']*100:.2f}  "
                f"{r['fnr_mean']*100:>5.2f}±{r['fnr_std']*100:.2f}  "
                f"{r['time_to_isolation_mean']:>5.1f}  "
                f"{r['final_search_hops_mean']:>8.2f}  "
                f"{r['final_search_success_mean']:>8.1f}%  "
                f"{r['final_apl_mean']:>6.4f}"
            )
    print()


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SCOPE Adversarial Resilience Runner')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: N=200, 3 seeds')
    parser.add_argument('--seeds', type=int, default=None,
                        help='Override number of seeds')
    parser.add_argument('--nodes', type=int, default=None,
                        help='Override number of nodes')
    parser.add_argument('--iterations', type=int, default=ITERATIONS,
                        help=f'Sim iterations per run (default: {ITERATIONS})')
    parser.add_argument('--out-dir', default='results',
                        help='Output directory for CSVs')
    parser.add_argument('--fig-dir', default='results/figures',
                        help='Output directory for figures')
    args = parser.parse_args()

    if args.quick:
        num_nodes = args.nodes or 200
        seeds = QUICK_SEEDS[:args.seeds] if args.seeds else QUICK_SEEDS
        iterations = 20
        print(f"[QUICK MODE] N={num_nodes}, {len(seeds)} seeds, {iterations} iterations")
    else:
        num_nodes = args.nodes or 500
        seeds = list(range(args.seeds)) if args.seeds else FULL_SEEDS
        iterations = args.iterations

    # Warm up Numba
    print("Warming up Numba JIT compiler…")
    from src.simulation import run_simulation_parameterized
    _ = run_simulation_parameterized(num_nodes=50, seed=0, iterations=3, verbose=False)
    print("JIT warm-up complete.\n")

    df_raw, df_summary = run_adversarial_sweep(
        num_nodes=num_nodes,
        seeds=seeds,
        iterations=iterations,
        out_dir=args.out_dir,
        figures_dir=args.fig_dir,
    )

    plot_adversarial_resilience(df_summary, args.fig_dir)
    print_adversarial_summary(df_summary)
    print(f"\nDone. Results in {args.out_dir}/\n")
