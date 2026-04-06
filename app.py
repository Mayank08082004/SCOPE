"""
SCOPE — Flask API
All endpoints consumed by the frontend dashboard.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import networkx as nx
import random
import numpy as np

from src.config import ALPHA, BETA, GAMMA, SEED, QUERY_TTL, NUM_SEARCH_QUERIES
from src.agent import PeerAgent
from src.simulation import initialize_graph, test_routing_performance, compute_metrics

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Global simulation state
# ---------------------------------------------------------------------------
state = {
    'graph':          None,   # nx.Graph
    'agents':         None,   # {node_id: PeerAgent}
    'num_nodes':      100,
    'initial_degree': 4,
    'history': {
        'apl':        [],
        'clustering': [],
    },
    'search': {               # populated by /api/search/test
        'baseline_hops':    None,
        'baseline_success': None,
        'final_hops':       None,
        'final_success':    None,
    },
}


def _require_graph():
    """Return (None, error_response) if graph not initialised, else (G, None)."""
    if state['graph'] is None:
        return None, (jsonify({'status': 'error', 'message': 'Graph not initialised'}), 400)
    return state['graph'], None


# ===========================================================================
# CONFIG
# ===========================================================================
@app.route('/api/config', methods=['GET'])
def get_config():
    """Return current simulation configuration including utility weights."""
    return jsonify({
        'num_nodes':      state['num_nodes'],
        'initial_degree': state['initial_degree'],
        'alpha':          ALPHA,
        'beta':           BETA,
        'gamma':          GAMMA,
        'query_ttl':      QUERY_TTL,
        'num_search_queries': NUM_SEARCH_QUERIES,
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update num_nodes and/or initial_degree before initialisation."""
    data = request.get_json(force=True)
    if 'num_nodes' in data:
        state['num_nodes'] = max(10, min(1000, int(data['num_nodes'])))
    if 'initial_degree' in data:
        state['initial_degree'] = max(2, min(20, int(data['initial_degree'])))
    return jsonify({'status': 'success', 'num_nodes': state['num_nodes'], 'initial_degree': state['initial_degree']})


# ===========================================================================
# GRAPH
# ===========================================================================
@app.route('/api/graph/initialize', methods=['POST'])
def api_initialize_graph():
    """
    Build a fresh Erdős–Rényi graph with the current config,
    initialise agents, and reset history.
    """
    try:
        random.seed(SEED)
        np.random.seed(SEED)

        G = initialize_graph(
            num_nodes=state['num_nodes'],
            initial_degree=state['initial_degree'],
            seed=SEED,
        )
        agents = {node: PeerAgent(node, G) for node in G.nodes()}

        state['graph']   = G
        state['agents']  = agents
        state['history'] = {'apl': [], 'clustering': []}
        state['search']  = {
            'baseline_hops': None, 'baseline_success': None,
            'final_hops':    None, 'final_success':    None,
        }

        degree_vals = list(dict(G.degree()).values())
        return jsonify({
            'status':     'success',
            'num_nodes':  G.number_of_nodes(),
            'num_edges':  G.number_of_edges(),
            'avg_degree': round(sum(degree_vals) / len(degree_vals), 2),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/graph/data', methods=['GET'])
def get_graph_data():
    """
    Return nodes (with degree & normalised size) and edges for canvas rendering.
    Caps at 500 nodes for performance — samples if larger.
    """
    G, err = _require_graph()
    if err:
        return err

    try:
        degree_dict = dict(G.degree())
        max_degree  = max(degree_dict.values()) if degree_dict else 1

        all_nodes = list(G.nodes())
        sample    = all_nodes if len(all_nodes) <= 500 else random.sample(all_nodes, 500)
        sample_set = set(sample)

        nodes = [
            {
                'id':     str(n),
                'degree': degree_dict[n],
                'size':   round(5 + (degree_dict[n] / max_degree) * 15, 2),
            }
            for n in sample
        ]
        edges = [
            {'source': str(e[0]), 'target': str(e[1])}
            for e in G.edges()
            if e[0] in sample_set and e[1] in sample_set
        ]

        return jsonify({
            'nodes':     nodes,
            'edges':     edges,
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================================================================
# METRICS
# ===========================================================================
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Return current snapshot of key network metrics."""
    G, err = _require_graph()
    if err:
        return err

    try:
        apl, cc     = compute_metrics(G)
        density     = nx.density(G)
        degree_vals = list(dict(G.degree()).values())
        avg_degree  = sum(degree_vals) / len(degree_vals) if degree_vals else 0

        return jsonify({
            'apl':                    apl,
            'clustering_coefficient': cc,
            'density':                round(density, 6),
            'avg_degree':             round(avg_degree, 2),
            'num_nodes':              G.number_of_nodes(),
            'num_edges':              G.number_of_edges(),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================================================================
# EVOLUTION
# ===========================================================================
@app.route('/api/evolution/step', methods=['POST'])
def evolution_step():
    """Run a single OODA evolution step (20 % of nodes activate)."""
    G, err = _require_graph()
    if err:
        return err

    try:
        agents      = state['agents']
        active_nodes = random.sample(list(G.nodes()), max(1, int(len(G.nodes()) * 0.2)))

        for node_id in active_nodes:
            agents[node_id].observe()
            agents[node_id].act()

        apl, cc = compute_metrics(G)
        state['history']['apl'].append(apl)
        state['history']['clustering'].append(cc)

        step = len(state['history']['apl'])
        return jsonify({
            'status':     'success',
            'apl':        apl,
            'clustering': cc,
            'step':       step,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/evolution/run', methods=['POST'])
def run_evolution():
    """
    Run multiple evolution steps in one request.
    Body: { "steps": N }  (1 ≤ N ≤ 100)
    """
    G, err = _require_graph()
    if err:
        return err

    try:
        data      = request.get_json(force=True) or {}
        num_steps = max(1, min(100, int(data.get('steps', 10))))
        agents    = state['agents']

        for _ in range(num_steps):
            active = random.sample(list(G.nodes()), max(1, int(len(G.nodes()) * 0.2)))
            for node_id in active:
                agents[node_id].observe()
                agents[node_id].act()

            apl, cc = compute_metrics(G)
            state['history']['apl'].append(apl)
            state['history']['clustering'].append(cc)

        total = len(state['history']['apl'])
        return jsonify({
            'status':             'success',
            'steps_completed':    num_steps,
            'total_steps':        total,
            'current_apl':        state['history']['apl'][-1],
            'current_clustering': state['history']['clustering'][-1],
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================================================================
# HISTORY
# ===========================================================================
@app.route('/api/history', methods=['GET'])
def get_history():
    """Return the full APL and clustering time-series."""
    return jsonify({
        'apl':        state['history']['apl'],
        'clustering': state['history']['clustering'],
        'steps':      len(state['history']['apl']),
    })


# ===========================================================================
# SEARCH  (new — previously missing)
# ===========================================================================
@app.route('/api/search/baseline', methods=['POST'])
def search_baseline():
    """
    Run a baseline routing test on the CURRENT graph state (before/early evolution).
    Stores results under state['search']['baseline_*'].
    Body (optional): { "num_queries": N, "ttl": T }
    """
    G, err = _require_graph()
    if err:
        return err

    try:
        data       = request.get_json(force=True) or {}
        num_q      = max(10, min(2000, int(data.get('num_queries', NUM_SEARCH_QUERIES))))
        ttl        = max(5,  min(100,  int(data.get('ttl',         QUERY_TTL))))

        avg_hops, success_rate = test_routing_performance(G, state['agents'], num_q, ttl)
        state['search']['baseline_hops']    = avg_hops
        state['search']['baseline_success'] = success_rate

        return jsonify({
            'status':       'success',
            'phase':        'baseline',
            'avg_hops':     avg_hops,
            'success_rate': success_rate,
            'num_queries':  num_q,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/test', methods=['POST'])
def search_test():
    """
    Run a routing test on the current (evolved) graph state.
    Stores results under state['search']['final_*'].
    Body (optional): { "num_queries": N, "ttl": T }
    """
    G, err = _require_graph()
    if err:
        return err

    try:
        data       = request.get_json(force=True) or {}
        num_q      = max(10, min(2000, int(data.get('num_queries', NUM_SEARCH_QUERIES))))
        ttl        = max(5,  min(100,  int(data.get('ttl',         QUERY_TTL))))

        avg_hops, success_rate = test_routing_performance(G, state['agents'], num_q, ttl)
        state['search']['final_hops']    = avg_hops
        state['search']['final_success'] = success_rate

        return jsonify({
            'status':       'success',
            'phase':        'final',
            'avg_hops':     avg_hops,
            'success_rate': success_rate,
            'num_queries':  num_q,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/results', methods=['GET'])
def get_search_results():
    """Return both baseline and final search results (null if not yet run)."""
    s = state['search']

    improvement = None
    if s['baseline_hops'] and s['final_hops'] and s['baseline_hops'] > 0:
        improvement = round(
            (s['baseline_hops'] - s['final_hops']) / s['baseline_hops'] * 100, 2
        )

    return jsonify({
        'baseline': {
            'avg_hops':     s['baseline_hops'],
            'success_rate': s['baseline_success'],
        },
        'final': {
            'avg_hops':     s['final_hops'],
            'success_rate': s['final_success'],
        },
        'improvement_pct': improvement,
    })


# ===========================================================================
# NODE
# ===========================================================================
@app.route('/api/node/<int:node_id>', methods=['GET'])
def get_node_info(node_id):
    """Return detailed info for a specific node."""
    G, err = _require_graph()
    if err:
        return err

    if node_id not in G.nodes():
        return jsonify({'status': 'error', 'message': f'Node {node_id} not found'}), 404

    try:
        agent     = state['agents'][node_id]
        degree    = G.degree(node_id)
        neighbors = list(G.neighbors(node_id))
        bandwidth = agent.calculate_bandwidth()

        # Utility scores for current neighbours
        neighbor_utilities = {
            str(n): round(agent.calculate_utility(n), 4)
            for n in neighbors
        }

        return jsonify({
            'id':                 node_id,
            'degree':             degree,
            'neighbors':          neighbors,
            'bandwidth':          round(bandwidth, 2),
            'memory_size':        len(agent.memory),
            'neighbor_utilities': neighbor_utilities,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/nodes/stats', methods=['GET'])
def get_nodes_stats():
    """
    Return degree + bandwidth for all nodes.
    Used by the frontend to render the bandwidth scatter chart.
    """
    G, err = _require_graph()
    if err:
        return err

    try:
        stats = [
            {
                'id':        node_id,
                'degree':    G.degree(node_id),
                'bandwidth': round(agent.calculate_bandwidth(), 2),
            }
            for node_id, agent in state['agents'].items()
        ]
        return jsonify({'status': 'success', 'nodes': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================================================================
# STATUS  (health-check)
# ===========================================================================
@app.route('/api/status', methods=['GET'])
def get_status():
    """Lightweight health-check — used by frontend on load."""
    G = state['graph']
    return jsonify({
        'initialized':    G is not None,
        'num_nodes':      state['num_nodes'],
        'initial_degree': state['initial_degree'],
        'steps_run':      len(state['history']['apl']),
        'search_done': {
            'baseline': state['search']['baseline_hops'] is not None,
            'final':    state['search']['final_hops']    is not None,
        },
    })


# ===========================================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
