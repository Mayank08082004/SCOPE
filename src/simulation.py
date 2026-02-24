import networkx as nx
import random
import numpy as np
from tqdm import tqdm
from src.config import NUM_NODES, INITIAL_DEGREE, SEED, ITERATIONS, REWIRING_PROB
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

    return G, history