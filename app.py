from flask import Flask, jsonify, request
from flask_cors import CORS
import networkx as nx
import random
import numpy as np
from src.config import ALPHA, BETA, GAMMA, SEED, QUERY_TTL, NUM_SEARCH_QUERIES
from src.agent import PeerAgent
from src.simulation import initialize_graph, test_routing_performance

app = Flask(__name__)
CORS(app)

# Global state
simulation_state = {
    'graph': None,
    'agents': None,
    'num_nodes': 500,
    'initial_degree': 4,
    'history': {'apl': [], 'clustering': []},
    'is_running': False
}

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current simulation configuration"""
    return jsonify({
        'num_nodes': simulation_state['num_nodes'],
        'initial_degree': simulation_state['initial_degree'],
        'alpha': ALPHA,
        'beta': BETA,
        'gamma': GAMMA
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update simulation configuration"""
    data = request.json
    if 'num_nodes' in data:
        simulation_state['num_nodes'] = max(10, min(1000, data['num_nodes']))
    if 'initial_degree' in data:
        simulation_state['initial_degree'] = max(2, min(20, data['initial_degree']))
    
    return jsonify({'status': 'success', 'config': simulation_state})

@app.route('/api/graph/initialize', methods=['POST'])
def initialize_new_graph():
    """Initialize a new random graph"""
    try:
        num_nodes = simulation_state['num_nodes']
        initial_degree = simulation_state['initial_degree']
        
        print(f"Initializing graph with {num_nodes} nodes, degree {initial_degree}")
        
        random.seed(SEED)
        np.random.seed(SEED)
        
        # Create graph
        G = nx.erdos_renyi_graph(n=num_nodes, p=initial_degree/num_nodes, seed=SEED)
        
        # Ensure connectivity
        if not nx.is_connected(G):
            components = list(nx.connected_components(G))
            for i in range(len(components)-1):
                u = random.choice(list(components[i]))
                v = random.choice(list(components[i+1]))
                G.add_edge(u, v)
        
        # Initialize agents
        agents = {node: PeerAgent(node, G) for node in G.nodes()}
        
        simulation_state['graph'] = G
        simulation_state['agents'] = agents
        simulation_state['history'] = {'apl': [], 'clustering': []}
        
        return jsonify({
            'status': 'success',
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/graph/data', methods=['GET'])
def get_graph_data():
    """Get graph nodes and edges for visualization"""
    try:
        if simulation_state['graph'] is None:
            return jsonify({'status': 'error', 'message': 'Graph not initialized'}), 400
        
        G = simulation_state['graph']
        nodes = []
        edges = []
        
        # Get node data with degree information
        degree_dict = dict(G.degree())
        max_degree = max(degree_dict.values()) if degree_dict else 1
        
        for node in G.nodes():
            degree = degree_dict.get(node, 0)
            nodes.append({
                'id': str(node),
                'degree': degree,
                'size': 5 + (degree / max_degree) * 15
            })
        
        # Get edge data
        for edge in G.edges():
            edges.append({
                'source': str(edge[0]),
                'target': str(edge[1])
            })
        
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current network metrics"""
    try:
        if simulation_state['graph'] is None:
            return jsonify({'status': 'error', 'message': 'Graph not initialized'}), 400
        
        G = simulation_state['graph']
        
        # Calculate metrics
        if nx.is_connected(G):
            apl = nx.average_shortest_path_length(G)
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            apl = nx.average_shortest_path_length(subgraph)
        
        cc = nx.average_clustering(G)
        density = nx.density(G)
        degree_dict = dict(G.degree())
        avg_degree = sum(degree_dict.values()) / len(degree_dict) if degree_dict else 0
        
        return jsonify({
            'apl': round(apl, 4),
            'clustering_coefficient': round(cc, 4),
            'density': round(density, 4),
            'avg_degree': round(avg_degree, 2),
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/evolution/step', methods=['POST'])
def evolution_step():
    """Run one evolution step"""
    try:
        if simulation_state['graph'] is None:
            return jsonify({'status': 'error', 'message': 'Graph not initialized'}), 400
        
        G = simulation_state['graph']
        agents = simulation_state['agents']
        
        # Single evolution step
        active_nodes = random.sample(list(G.nodes()), int(len(G.nodes()) * 0.2))
        
        for node_id in active_nodes:
            agent = agents[node_id]
            agent.observe()
            agent.act()
        
        # Record metrics
        if nx.is_connected(G):
            apl = nx.average_shortest_path_length(G)
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            apl = nx.average_shortest_path_length(subgraph)
        
        cc = nx.average_clustering(G)
        simulation_state['history']['apl'].append(apl)
        simulation_state['history']['clustering'].append(cc)
        
        return jsonify({
            'status': 'success',
            'apl': round(apl, 4),
            'clustering': round(cc, 4),
            'step': len(simulation_state['history']['apl'])
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/evolution/run', methods=['POST'])
def run_evolution():
    """Run multiple evolution steps"""
    try:
        if simulation_state['graph'] is None:
            return jsonify({'status': 'error', 'message': 'Graph not initialized'}), 400
        
        data = request.json
        num_steps = data.get('steps', 10)
        num_steps = max(1, min(100, num_steps))
        
        G = simulation_state['graph']
        agents = simulation_state['agents']
        
        for step in range(num_steps):
            active_nodes = random.sample(list(G.nodes()), int(len(G.nodes()) * 0.2))
            
            for node_id in active_nodes:
                agent = agents[node_id]
                agent.observe()
                agent.act()
            
            # Record metrics
            if nx.is_connected(G):
                apl = nx.average_shortest_path_length(G)
            else:
                largest_cc = max(nx.connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc)
                apl = nx.average_shortest_path_length(subgraph)
            
            cc = nx.average_clustering(G)
            simulation_state['history']['apl'].append(apl)
            simulation_state['history']['clustering'].append(cc)
        
        return jsonify({
            'status': 'success',
            'steps_completed': num_steps,
            'current_apl': round(simulation_state['history']['apl'][-1], 4),
            'current_clustering': round(simulation_state['history']['clustering'][-1], 4),
            'total_steps': len(simulation_state['history']['apl'])
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get metrics history"""
    return jsonify({
        'apl': simulation_state['history']['apl'],
        'clustering': simulation_state['history']['clustering']
    })

@app.route('/api/node/<int:node_id>', methods=['GET'])
def get_node_info(node_id):
    """Get detailed information about a specific node"""
    try:
        if simulation_state['graph'] is None:
            return jsonify({'status': 'error', 'message': 'Graph not initialized'}), 400
        
        G = simulation_state['graph']
        agents = simulation_state['agents']
        
        if node_id not in G.nodes():
            return jsonify({'status': 'error', 'message': 'Node not found'}), 404
        
        agent = agents[node_id]
        degree = G.degree(node_id)
        neighbors = list(G.neighbors(node_id))
        bandwidth = agent.calculate_bandwidth()
        
        return jsonify({
            'id': node_id,
            'degree': degree,
            'neighbors': neighbors,
            'bandwidth': round(bandwidth, 2),
            'memory_size': len(agent.memory)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get simulation status"""
    return jsonify({
        'initialized': simulation_state['graph'] is not None,
        'num_nodes': simulation_state['num_nodes'],
        'initial_degree': simulation_state['initial_degree']
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000
)