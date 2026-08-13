import random
import numpy as np
import networkx as nx
from tqdm import tqdm

from src.config import (
    NUM_NODES, INITIAL_DEGREE, SEED,
    ITERATIONS, REWIRING_PROB,
    QUERY_TTL, NUM_SEARCH_QUERIES,
)
from src.agent import PeerAgent


# -----------------------------------------------------------------------
# Graph initialisation
# -----------------------------------------------------------------------
def initialize_graph(num_nodes=NUM_NODES, initial_degree=INITIAL_DEGREE, seed=SEED):
    """Create and return a connected Erdős–Rényi random graph."""
    print(f">>> Initializing Random Graph — {num_nodes} nodes, avg degree {initial_degree}")
    G = nx.erdos_renyi_graph(n=num_nodes, p=initial_degree / num_nodes, seed=seed)

    # Guarantee connectivity by bridging disconnected components
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            u = random.choice(list(components[i]))
            v = random.choice(list(components[i + 1]))
            G.add_edge(u, v)

    return G


# -----------------------------------------------------------------------
# Routing / search evaluation
# -----------------------------------------------------------------------
def test_routing_performance(G, agents, num_queries=NUM_SEARCH_QUERIES, ttl=QUERY_TTL):
    """
    Evaluate search efficiency using trained agent memory + gradient-ascent fallback.
    Returns (avg_hops, success_rate_pct).
    """
    print(f"\n>>> Running {num_queries} Smart Search Queries…")

    success_count = 0
    total_hops    = 0
    nodes         = list(G.nodes())

    for _ in range(num_queries):
        source = random.choice(nodes)
        target = random.choice(nodes)
        if source == target:
            continue

        curr_node = source
        path      = [source]
        found     = False

        for _ in range(ttl):
            agent = agents[curr_node]

            # 1. Memory-assisted shortcut
            if target in agent.memory:
                if target in list(G.neighbors(curr_node)):
                    path.append(target)
                    found = True
                    break
                # target is a friend-of-friend — find bridge neighbour
                bridge = next(
                    (n for n in G.neighbors(curr_node) if target in G.neighbors(n)),
                    None,
                )
                if bridge:
                    path.extend([bridge, target])
                    found = True
                break

            # 2. Gradient-ascent fallback
            neighbors       = list(G.neighbors(curr_node))
            valid_neighbors = [n for n in neighbors if n not in path]
            if not valid_neighbors:
                break

            next_node = max(valid_neighbors, key=lambda n: G.degree(n))
            path.append(next_node)
            curr_node = next_node

            if curr_node == target:
                found = True
                break

        if found:
            success_count += 1
            total_hops    += len(path) - 1

    avg_hops     = total_hops / success_count if success_count > 0 else 0.0
    success_rate = (success_count / num_queries) * 100

    return round(avg_hops, 4), round(success_rate, 2)


# -----------------------------------------------------------------------
# Network metrics helper
# -----------------------------------------------------------------------
def compute_metrics(G):
    """Return APL and average clustering for G (uses largest CC if disconnected)."""
    if nx.is_connected(G):
        apl = nx.average_shortest_path_length(G)
    else:
        sub = G.subgraph(max(nx.connected_components(G), key=len))
        apl = nx.average_shortest_path_length(sub)

    cc = nx.average_clustering(G)
    return round(apl, 6), round(cc, 6)


# -----------------------------------------------------------------------
# Full offline simulation  (used by main.py)
# -----------------------------------------------------------------------
def run_simulation():
    random.seed(SEED)
    np.random.seed(SEED)

    G      = initialize_graph()
    agents = {node: PeerAgent(node, G) for node in G.nodes()}

    history = {
        'apl':        [],
        'clustering': [],
    }

    # Baseline search (before evolution)
    print("\n>>> Phase 1 — Baseline Search (Random Graph)")
    baseline_hops, baseline_sr = test_routing_performance(G, agents)
    history['baseline_search_hops']    = baseline_hops
    history['baseline_search_success'] = baseline_sr

    # Evolution loop
    print(f"\n>>> Phase 2 — Evolutionary Simulation ({ITERATIONS} steps)")
    for step in tqdm(range(ITERATIONS)):
        active = random.sample(list(G.nodes()), int(NUM_NODES * REWIRING_PROB))
        for node_id in active:
            agents[node_id].observe()
            agents[node_id].act()

        apl, cc = compute_metrics(G)
        history['apl'].append(apl)
        history['clustering'].append(cc)

    # Final search (after evolution)
    final_hops, final_sr = test_routing_performance(G, agents)
    history['final_search_hops']   = final_hops
    history['search_success_rate'] = final_sr

    # Per-node incentive stats
    history['node_stats'] = [
        {
            'id':        node_id,
            'degree':    G.degree(node_id),
            'bandwidth': round(agent.calculate_bandwidth(), 4),
        }
        for node_id, agent in agents.items()
    ]

    return G, history
