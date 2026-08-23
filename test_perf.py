import time
from app import state, runtime_config, _execute_parallel_step
from src.simulation import initialize_graph
import random
from src.agent import PeerAgent

print("Init graph...")
G = initialize_graph(num_nodes=1000, initial_degree=4, seed=42)
agents = {node: PeerAgent(node, G, False) for node in G.nodes()}

active_nodes = random.sample(list(G.nodes()), 200)

print("Running parallel...")
start = time.time()
_execute_parallel_step(G, agents, active_nodes)
print("Parallel time:", time.time() - start)

def _sync_step(G, agents, active_nodes):
    for node_id in active_nodes:
        agent = agents[node_id]
        drop, add, new_mem = agent.decide(
            alpha=runtime_config['alpha'],
            beta=runtime_config['beta'],
            gamma=runtime_config['gamma'],
            bw_weight=runtime_config['betweenness_weight']
        )
        agent.memory = new_mem
        if drop and G.has_edge(agent_id, drop):
            G.remove_edge(agent_id, drop)
        if add:
            G.add_edge(agent_id, add)

print("Running sync...")
start = time.time()
_sync_step(G, agents, active_nodes)
print("Sync time:", time.time() - start)
