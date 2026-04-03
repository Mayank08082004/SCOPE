import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
from src.simulation import run_simulation

def plot_results(final_graph, metrics_history):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Plot 1: Efficiency (APL)
    axes[0, 0].plot(metrics_history['apl'], marker='o', color='b', linewidth=2)
    axes[0, 0].set_title("Optimization of Routing Efficiency")
    axes[0, 0].set_xlabel("Simulation Steps")
    axes[0, 0].set_ylabel("Avg. Path Length (Hops)")
    axes[0, 0].grid(True)

    # Plot 2: Clustering
    axes[0, 1].plot(metrics_history['clustering'], marker='s', color='g', linewidth=2)
    axes[0, 1].set_title("Emergence of Social Clustering")
    axes[0, 1].set_xlabel("Simulation Steps")
    axes[0, 1].set_ylabel("Clustering Coefficient")
    axes[0, 1].grid(True)

    # Plot 3: Adjacency Heatmap (Core-Periphery)
    degree_sequence = sorted(final_graph.degree, key=lambda x: x[1], reverse=True)
    sorted_nodes = [n for n, d in degree_sequence]
    adj_matrix = nx.to_numpy_array(final_graph, nodelist=sorted_nodes)
    sns.heatmap(adj_matrix[:100, :100], ax=axes[1, 0], cmap="Greys", cbar=False)
    axes[1, 0].set_title("Adjacency Matrix (Top 100 Nodes)")
    axes[1, 0].set_xlabel("Node Rank (Degree)")
    axes[1, 0].set_ylabel("Node Rank (Degree)")

    # Plot 4: Incentive Mechanism (Logistic Bandwidth)
    node_degrees = [s['degree'] for s in metrics_history['node_stats']]
    node_bandwidths = [s['bandwidth'] for s in metrics_history['node_stats']]
    axes[1, 1].scatter(node_degrees, node_bandwidths, alpha=0.5, color='orange')
    axes[1, 1].set_title("Incentive Mechanism: Degree vs. Bandwidth")
    axes[1, 1].set_xlabel("Node Degree (Centrality)")
    axes[1, 1].set_ylabel("Download Speed (Mbps)")
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Run the Simulation
    G, history = run_simulation()

    # Print Final Stats
    print("\n" + "="*40)
    print("      PHASE 2: OPERATIONAL RESULTS")
    print("="*40)
    
    print(f"\n[1] Search Efficiency (Gradient Ascent):")
    print(f"  - Baseline (Random): {history['baseline_search_hops']:.2f} hops ({history['baseline_search_success']:.1f}% success)")
    print(f"  - Strategic (Trained): {history['final_search_hops']:.2f} hops ({history['search_success_rate']:.1f}% success)")
    
    improvement = (history['baseline_search_hops'] - history['final_search_hops']) / history['baseline_search_hops'] * 100
    print(f"  - Performance Gain: {improvement:.2f}% reduction in path length")

    print(f"\n[2] Incentive Mechanism (Differential Service):")
    core_bw = np.mean([s['bandwidth'] for s in history['node_stats'] if s['degree'] > 10])
    leaf_bw = np.mean([s['bandwidth'] for s in history['node_stats'] if s['degree'] <= 3])
    print(f"  - Avg Core Hub Bandwidth: {core_bw:.2f} Mbps")
    print(f"  - Avg Leaf Node Bandwidth: {leaf_bw:.2f} Mbps")
    print(f"  - Service Multiplier: {core_bw/leaf_bw:.1f}x faster for hubs")

    print("\n>>> Network Evolution:")
    print(f"  - Final Avg Path Length: {history['apl'][-1]:.4f}")
    print(f"  - Final Clustering Coeff: {history['clustering'][-1]:.4f}")
    
    # Visualize
    plot_results(G, history)