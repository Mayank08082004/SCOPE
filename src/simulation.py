import random
import numpy as np
import networkx as nx
from tqdm import tqdm

from src.config import (
    NUM_NODES, INITIAL_DEGREE, SEED,
    ITERATIONS, REWIRING_PROB,
    QUERY_TTL, NUM_SEARCH_QUERIES,
    CHURN_RATE, CHURN_INTERVAL,
    DEFECTOR_RATIO, ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT
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
# Churn Logic
# -----------------------------------------------------------------------
def apply_churn(G, agents, sleeping_nodes, max_node_id, churn_rate=CHURN_RATE, temp_ratio=0.5, defector_ratio=DEFECTOR_RATIO):
    """
    Applies network churn.
    temp_ratio: fraction of churned nodes that just go to sleep (the rest permanently leave)
    """
    # 1. Wake up currently sleeping nodes
    for node_id, agent in list(sleeping_nodes.items()):
        G.add_node(node_id)
        agents[node_id] = agent
        
        active_nodes = list(G.nodes())
        active_nodes.remove(node_id)
        
        # Connect to old memory if alive, else random
        alive_memory = [n for n in agent.memory if G.has_node(n)]
        targets = alive_memory if alive_memory else active_nodes
        if targets:
            num_conns = min(INITIAL_DEGREE, len(targets))
            for t in random.sample(targets, num_conns):
                G.add_edge(node_id, t)
                
        del sleeping_nodes[node_id]

    # 2. Select nodes to churn
    nodes = list(G.nodes())
    num_to_churn = int(len(nodes) * churn_rate)
    if num_to_churn == 0:
        return max_node_id

    churn_candidates = random.sample(nodes, num_to_churn)
    
    for node_id in churn_candidates:
        if random.random() < temp_ratio:
            # Temporary sleep
            sleeping_nodes[node_id] = agents[node_id]
            G.remove_node(node_id)
            del agents[node_id]
        else:
            # Permanent leave
            G.remove_node(node_id)
            del agents[node_id]
            
            # Replace with a new node
            max_node_id += 1
            new_id = max_node_id
            G.add_node(new_id)
            is_defector = random.random() < defector_ratio
            agents[new_id] = PeerAgent(new_id, G, is_defector=is_defector)
            G.nodes[new_id]['is_defector'] = is_defector
            
            active_nodes = list(G.nodes())
            active_nodes.remove(new_id)
            if active_nodes:
                num_conns = min(INITIAL_DEGREE, len(active_nodes))
                targets = random.sample(active_nodes, num_conns)
                for t in targets:
                    G.add_edge(new_id, t)
                    
    # 3. Ensure connectivity
    if not nx.is_connected(G) and len(G.nodes()) > 1:
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            u = random.choice(list(components[i]))
            v = random.choice(list(components[i + 1]))
            G.add_edge(u, v)

    return max_node_id


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
    """Return APL and average clustering for G (uses largest CC if disconnected).
    Approximates APL for large graphs to prevent server hangs.
    """
    if len(G) == 0:
        return 0, 0
        
    sub = G if nx.is_connected(G) else G.subgraph(max(nx.connected_components(G), key=len))
    
    if len(sub) > 1000:
        # Approximate APL by sampling
        sample_nodes = random.sample(list(sub.nodes()), 100)
        path_lengths = []
        for node in sample_nodes:
            lengths = nx.single_source_shortest_path_length(sub, node)
            path_lengths.extend(lengths.values())
        apl = sum(path_lengths) / len(path_lengths) if path_lengths else 0
    else:
        apl = nx.average_shortest_path_length(sub)

    # Clustering coefficient approximation is built into NetworkX natively by using 
    # the average_clustering but we can also sample if needed. 
    # nx.average_clustering takes a nodes= kwarg for sampling
    if len(G) > 1000:
        sample_nodes = random.sample(list(G.nodes()), 100)
        cc = nx.average_clustering(G, nodes=sample_nodes)
    else:
        cc = nx.average_clustering(G)
        
    return round(apl, 6), round(cc, 6)


# -----------------------------------------------------------------------
# Full offline simulation  (used by main.py)
# -----------------------------------------------------------------------
def run_simulation():
    random.seed(SEED)
    np.random.seed(SEED)

    G      = initialize_graph()
    
    agents = {}
    for node in G.nodes():
        is_defector = random.random() < DEFECTOR_RATIO
        agents[node] = PeerAgent(node, G, is_defector=is_defector)
        G.nodes[node]['is_defector'] = is_defector

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
    sleeping_nodes = {}
    max_node_id = max(G.nodes()) if G.nodes() else 0

    for step in tqdm(range(ITERATIONS)):
        # Apply churn every CHURN_INTERVAL steps
        if step > 0 and step % CHURN_INTERVAL == 0:
            max_node_id = apply_churn(G, agents, sleeping_nodes, max_node_id)

        k = max(10, int(len(G.nodes()) * 0.1))
        bc = nx.betweenness_centrality(G, k=k)
        nx.set_node_attributes(G, bc, 'betweenness')

        active = random.sample(list(G.nodes()), int(len(G.nodes()) * REWIRING_PROB))
        
        # Sequential OODA loop — Numba @njit handles inner-loop speed;
        # multiprocessing was removed due to fork-safety issues with NetworkX
        # graph objects on macOS (pickling fails for large graphs).
        for node_id in active:
            agent = agents[node_id]
            _, drop, add, new_mem = agent.decide(
                alpha=ALPHA,
                beta=BETA,
                gamma=GAMMA,
                bw_weight=BETWEENNESS_WEIGHT,
                delta=DELTA_WEIGHT
            )
            agent.memory = new_mem
            if drop and G.has_edge(node_id, drop):
                G.remove_edge(node_id, drop)
            if add:
                G.add_edge(node_id, add)

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


# -----------------------------------------------------------------------
# Parameterized simulation  (used by ablation_runner — no churn)
# -----------------------------------------------------------------------
def run_simulation_parameterized(
    alpha=ALPHA,
    beta=BETA,
    gamma=GAMMA,
    bw_weight=BETWEENNESS_WEIGHT,
    delta=DELTA_WEIGHT,
    num_nodes=NUM_NODES,
    seed=SEED,
    iterations=ITERATIONS,
    rewiring_prob=REWIRING_PROB,
    num_queries=NUM_SEARCH_QUERIES,
    ttl=QUERY_TTL,
    defector_ratio=DEFECTOR_RATIO,
    verbose=False,
):
    """
    Churn-free, fully parameterized simulation for ablation studies.

    Churn is intentionally excluded: it introduces stochastic node-count
    drift that confounds single-variable comparisons across seeds and makes
    metric curves noisy for publication.

    Returns a flat dict of scalar summary metrics (not the full graph):
        {
            'final_apl':          float,
            'initial_apl':        float,
            'final_clustering':   float,
            'initial_clustering': float,
            'apl_reduction_pct':  float,
            'final_search_hops':  float,
            'search_success_pct': float,
            'avg_bw_hub':         float,  # mean bandwidth for degree > 10
            'avg_bw_leaf':        float,  # mean bandwidth for degree <= 3
            'bw_multiplier':      float,  # hub / leaf ratio
        }
    """
    random.seed(seed)
    np.random.seed(seed)

    G = initialize_graph(num_nodes=num_nodes, initial_degree=INITIAL_DEGREE, seed=seed)

    agents = {}
    for node in G.nodes():
        is_def = random.random() < defector_ratio
        agents[node] = PeerAgent(node, G, is_defector=is_def)
        G.nodes[node]['is_defector'] = is_def

    # Initial metrics
    initial_apl, initial_cc = compute_metrics(G)

    history_apl = [initial_apl]
    history_cc  = [initial_cc]

    itr = tqdm(range(iterations), desc=f"N={num_nodes} α={alpha} β={beta} γ={gamma} δ={delta} s={seed}",
               leave=False, disable=not verbose)

    for _ in itr:
        # Approximate betweenness with very small k for ablation speed
        # k=20 gives stable approximate rankings; full k=N would be O(VE).
        k_bc = max(10, min(20, num_nodes // 250))
        bc   = nx.betweenness_centrality(G, k=k_bc)
        nx.set_node_attributes(G, bc, 'betweenness')

        active = random.sample(list(G.nodes()), int(len(G.nodes()) * rewiring_prob))

        for node_id in active:
            agent = agents[node_id]
            _, drop, add, new_mem = agent.decide(
                alpha=alpha,
                beta=beta,
                gamma=gamma,
                bw_weight=bw_weight,
                delta=delta,
            )
            agent.memory = new_mem
            if drop and G.has_edge(node_id, drop):
                G.remove_edge(node_id, drop)
            if add:
                G.add_edge(node_id, add)

        apl, cc = compute_metrics(G)
        history_apl.append(apl)
        history_cc.append(cc)

    # Search performance (50 queries — sufficient for ablation trend comparison)
    final_hops, success_pct = test_routing_performance(
        G, agents, num_queries=min(num_queries, 50), ttl=ttl
    )

    # Bandwidth incentive stats
    bws = [(G.degree(nid), agent.calculate_bandwidth()) for nid, agent in agents.items()]
    hub_bws  = [bw for deg, bw in bws if deg > 10]
    leaf_bws = [bw for deg, bw in bws if deg <= 3]
    avg_hub  = float(np.mean(hub_bws))  if hub_bws  else 0.0
    avg_leaf = float(np.mean(leaf_bws)) if leaf_bws else 0.0
    bw_mult  = avg_hub / avg_leaf if avg_leaf > 0 else 0.0

    return {
        'initial_apl':        initial_apl,
        'final_apl':          history_apl[-1],
        'apl_history':        history_apl,
        'initial_clustering': initial_cc,
        'final_clustering':   history_cc[-1],
        'cc_history':         history_cc,
        'apl_reduction_pct':  (initial_apl - history_apl[-1]) / initial_apl * 100 if initial_apl > 0 else 0.0,
        'final_search_hops':  final_hops,
        'search_success_pct': success_pct,
        'avg_bw_hub':         avg_hub,
        'avg_bw_leaf':        avg_leaf,
        'bw_multiplier':      bw_mult,
    }
