import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
from src.simulation import run_simulation

def plot_results(final_graph, metrics_history):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Plot 1: Efficiency (APL)
    axes[0].plot(metrics_history['apl'], marker='o', color='b', linewidth=2)
    axes[0].set_title("Optimization of Routing Efficiency")
    axes[0].set_xlabel("Simulation Steps")
    axes[0].set_ylabel("Avg. Path Length (Hops)")
    axes[0].grid(True)

    # Plot 2: Clustering
    axes[1].plot(metrics_history['clustering'], marker='s', color='g', linewidth=2)
    axes[1].set_title("Emergence of Social Clustering")
    axes[1].set_xlabel("Simulation Steps")
    axes[1].set_ylabel("Clustering Coefficient")
    axes[1].grid(True)

    # Plot 3: Adjacency Heatmap
    degree_sequence = sorted(final_graph.degree, key=lambda x: x[1], reverse=True)
    sorted_nodes = [n for n, d in degree_sequence]
    adj_matrix = nx.to_numpy_array(final_graph, nodelist=sorted_nodes)

    sns.heatmap(adj_matrix[:100, :100], ax=axes[2], cmap="Greys", cbar=False)
    axes[2].set_title("Adjacency Matrix (Top 100 Nodes)")
    axes[2].set_xlabel("Node Rank (Degree)")
    axes[2].set_ylabel("Node Rank (Degree)")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Run the Simulation
    G, history = run_simulation()

    # Print Final Stats
    print("\n>>> Final Network Status:")
    print(f"Final Avg Path Length: {history['apl'][-1]:.4f}")
    print(f"Final Clustering Coeff: {history['clustering'][-1]:.4f}")

    print("\n>>> Phase 2: Operational Search Results:")
    print(f"Gradient Ascent Search Success Rate: {history['search_success_rate']:.2f}%")
    print(f"Average Hops to Find File: {history['final_search_hops']:.4f}")
    
    # Visualize
    plot_results(G, history)