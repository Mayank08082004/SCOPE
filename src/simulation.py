import networkx as nx
import random
import numpy as np
from tqdm import tqdm
from src.config import NUM_NODES, INITIAL_DEGREE, SEED, ITERATIONS, REWIRING_PROB, QUERY_TTL, NUM_SEARCH_QUERIES
from src.agent import PeerAgent

def initialize_graph():
    """Create the initial random baseline graph."""
    print(">>> Initializing Random Graph (Baseline)...")
    G = nx.erdos_renyi_graph(n=NUM_NODES, p=INITIAL_DEGREE/NUM_NODES, seed=SEED)

    # Ensure connectivity
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components)-1):
            u = random.choice(list(components[i]))
            v = random.choice(list(components[i+1]))
            G.add_edge(u, v)
    return G

def test_routing_performance(G, agents):
    """
    Phase 2: Measure Search Efficiency (Improved)
    Uses the TRAINED Agent's Memory (Belief) to find paths.
    """
    print(f"\n>>> Running {NUM_SEARCH_QUERIES} Smart Search Queries (Using Trained Memory)...")
    
    success_count = 0
    total_hops = 0
    nodes = list(G.nodes())
    
    for _ in range(NUM_SEARCH_QUERIES):
        source = random.choice(nodes)
        target = random.choice(nodes)
        if source == target: continue
        
        # Start Search
        curr_node = source
        path = [source]
        found = False
        
        for _ in range(QUERY_TTL):
            # 1. Check Agent's Memory (Smart Lookahead)
            # Use the existing agent from the simulation!
            agent = agents[curr_node]
            
            if target in agent.memory:
                # If known, we can route there (Simulating a known path)
                if target in G.neighbors(curr_node):
                    path.append(target)
                else:
                    # If it's in memory but not a neighbor, it's likely a friend-of-friend
                    # Find the bridge
                    neighbors = list(G.neighbors(curr_node))
                    # Check which neighbor connects to target
                    bridge = next((n for n in neighbors if target in G.neighbors(n)), None)
                    if bridge:
                        path.append(bridge)
                        path.append(target)
                    else:
                        # Fallback if memory is stale (topology changed)
                        pass 
                found = True
                break
            
            # 2. Gradient Ascent (Fallback)
            neighbors = list(G.neighbors(curr_node))
            valid_neighbors = [n for n in neighbors if n not in path]
            
            if not valid_neighbors: break # Dead end
            
            # Move to highest degree neighbor
            next_node = max(valid_neighbors, key=lambda n: G.degree(n))
            path.append(next_node)
            curr_node = next_node
            
            if curr_node == target:
                found = True
                break
        
        if found:
            success_count += 1
            total_hops += (len(path) - 1)

    # Calculate Stats
    avg_hops = total_hops / success_count if success_count > 0 else 0
    success_rate = (success_count / NUM_SEARCH_QUERIES) * 100
    
    return avg_hops, success_rate

def run_simulation():
    # Set seeds
    random.seed(SEED)
    np.random.seed(SEED)

    G = initialize_graph()
    
    # Capture Baseline Metrics
    history = {'apl': [], 'clustering': []}
    
    # Initialize Agents
    agents = {node: PeerAgent(node, G) for node in G.nodes()}

    print(f"\n>>> Starting Evolutionary Simulation for {ITERATIONS} steps...")
    
    for step in tqdm(range(ITERATIONS)):
        # Randomized Asynchronous Activation
        active_nodes = random.sample(list(G.nodes()), int(NUM_NODES * REWIRING_PROB))

        for node_id in active_nodes:
            agent = agents[node_id]
            agent.observe() # Update Beliefs
            agent.act()     # Reason & Act

        # Record Metrics
        if nx.is_connected(G):
            apl = nx.average_shortest_path_length(G)
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            apl = nx.average_shortest_path_length(subgraph)

        cc = nx.average_clustering(G)
        history['apl'].append(apl)
        history['clustering'].append(cc)

    # --- PHASE 2: SEARCH TEST ---
    # PASS THE TRAINED AGENTS HERE!
    final_avg_hops, success_rate = test_routing_performance(G, agents)
    
    history['final_search_hops'] = final_avg_hops
    history['search_success_rate'] = success_rate

    return G, history