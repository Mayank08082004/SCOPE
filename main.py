"""
SCOPE — offline CLI runner
Runs the full simulation and renders matplotlib plots.
Use this when you want a full end-to-end batch run
without starting the Flask server.
"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

from src.simulation import run_simulation


# ---------------------------------------------------------------------------
def plot_results(final_graph, history):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("SCOPE — P2P Network Simulation Results", fontsize=14, y=1.01)

    # 1. Routing efficiency (APL)
    axes[0, 0].plot(history['apl'], marker='o', color='#378ADD', linewidth=2, markersize=3)
    axes[0, 0].set_title("Routing Efficiency (Avg Path Length)")
    axes[0, 0].set_xlabel("Simulation Step")
    axes[0, 0].set_ylabel("Avg Path Length (hops)")
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Clustering coefficient
    axes[0, 1].plot(history['clustering'], marker='s', color='#1D9E75', linewidth=2, markersize=3)
    axes[0, 1].set_title("Emergence of Social Clustering")
    axes[0, 1].set_xlabel("Simulation Step")
    axes[0, 1].set_ylabel("Clustering Coefficient")
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Adjacency heatmap (core–periphery, top 100 nodes by degree)
    degree_seq  = sorted(final_graph.degree, key=lambda x: x[1], reverse=True)
    sorted_nodes = [n for n, _ in degree_seq]
    adj_matrix   = nx.to_numpy_array(final_graph, nodelist=sorted_nodes)
    sns.heatmap(adj_matrix[:100, :100], ax=axes[1, 0], cmap="Blues", cbar=False)
    axes[1, 0].set_title("Adjacency Matrix — Top 100 Nodes by Degree")
    axes[1, 0].set_xlabel("Node Rank (degree)")
    axes[1, 0].set_ylabel("Node Rank (degree)")

    # 4. Incentive mechanism (degree vs bandwidth)
    node_degrees    = [s['degree']    for s in history['node_stats']]
    node_bandwidths = [s['bandwidth'] for s in history['node_stats']]
    axes[1, 1].scatter(node_degrees, node_bandwidths, alpha=0.4, color='#D85A30', s=15)
    axes[1, 1].set_title("Incentive: Degree vs Download Bandwidth")
    axes[1, 1].set_xlabel("Node Degree (centrality)")
    axes[1, 1].set_ylabel("Download Speed (Mbps)")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("scope_results.png", dpi=150, bbox_inches='tight')
    print("\n>>> Plot saved to scope_results.png")
    plt.show()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    G, history = run_simulation()

    print("\n" + "=" * 50)
    print("         SCOPE — FINAL SIMULATION RESULTS")
    print("=" * 50)

    print("\n[1] Search Efficiency (Gradient Ascent Routing):")
    print(f"    Baseline  (random):  {history['baseline_search_hops']:.2f} hops  "
          f"({history['baseline_search_success']:.1f}% success)")
    print(f"    Strategic (trained): {history['final_search_hops']:.2f} hops  "
          f"({history['search_success_rate']:.1f}% success)")

    if history['baseline_search_hops'] > 0:
        gain = (
            (history['baseline_search_hops'] - history['final_search_hops'])
            / history['baseline_search_hops'] * 100
        )
        print(f"    Performance gain:    {gain:.2f}% reduction in path length")

    print("\n[2] Incentive Mechanism (Differential Service):")
    core_bw = np.mean([s['bandwidth'] for s in history['node_stats'] if s['degree'] > 10])
    leaf_bw = np.mean([s['bandwidth'] for s in history['node_stats'] if s['degree'] <= 3])
    if leaf_bw > 0:
        print(f"    Avg core-hub bandwidth : {core_bw:.2f} Mbps")
        print(f"    Avg leaf-node bandwidth: {leaf_bw:.2f} Mbps")
        print(f"    Service multiplier     : {core_bw / leaf_bw:.1f}× faster for hubs")

    print("\n[3] Network Evolution:")
    if history['apl']:
        print(f"    Final avg path length  : {history['apl'][-1]:.4f}")
        print(f"    Final clustering coeff : {history['clustering'][-1]:.4f}")

    plot_results(G, history)
