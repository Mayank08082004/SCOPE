"""
SCOPE — Flask API
All endpoints consumed by the frontend dashboard.

FIX LOG
-------
* /api/config POST now accepts alpha, beta, gamma, query_ttl, num_search_queries
  and stores them in runtime_config (module-level import overrides no longer needed).
* /api/search/baseline and /api/search/test pass runtime_config values to
  test_routing_performance, fixing the 500 errors.
* test_routing_performance wrapped in a try/except per-query so one bad node
  never kills the whole evaluation.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import networkx as nx
import random
import numpy as np

from src.config import (
    ALPHA as DEFAULT_ALPHA,
    BETA  as DEFAULT_BETA,
    GAMMA as DEFAULT_GAMMA,
    SEED,
    QUERY_TTL          as DEFAULT_QUERY_TTL,
    NUM_SEARCH_QUERIES as DEFAULT_NUM_SEARCH_QUERIES,
)
from src.agent import PeerAgent
from src.simulation import initialize_graph, compute_metrics

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Runtime config — mutable at runtime via /api/config POST
# ---------------------------------------------------------------------------
runtime_config = {
    'alpha':              DEFAULT_ALPHA,
    'beta':               DEFAULT_BETA,
    'gamma':              DEFAULT_GAMMA,
    'query_ttl':          DEFAULT_QUERY_TTL,
    'num_search_queries': DEFAULT_NUM_SEARCH_QUERIES,
}

# ---------------------------------------------------------------------------
# Global simulation state
# ---------------------------------------------------------------------------
state = {
    'graph':          None,
    'agents':         None,
    'num_nodes':      100,
    'initial_degree': 4,
    'history': {
        'apl':        [],
        'clustering': [],
    },
    'search': {
        'baseline_hops':    None,
        'baseline_success': None,
        'final_hops':       None,
        'final_success':    None,
    },
}


def _require_graph():
    if state['graph'] is None:
        return None, (jsonify({'status': 'error', 'message': 'Graph not initialised'}), 400)
    return state['graph'], None


# ---------------------------------------------------------------------------
# Routing evaluation — fixed to guard against missing agents / bad nodes
# ---------------------------------------------------------------------------
def _test_routing_performance(G, agents, num_queries, ttl):
    """
    Evaluate search efficiency.  Robust version that catches per-query
    exceptions so one bad traversal doesn't abort the whole test.
    Returns (avg_hops, success_rate_pct).
    """
    success_count = 0
    total_hops    = 0
    nodes         = list(G.nodes())

    if len(nodes) < 2:
        return 0.0, 0.0

    for _ in range(num_queries):
        try:
            source = random.choice(nodes)
            target = random.choice(nodes)
            if source == target:
                continue

            curr_node = source
            path      = [source]
            found     = False

            for _ in range(ttl):
                # Guard: skip if node was removed from graph
                if curr_node not in G:
                    break

                # Guard: agent must exist
                agent = agents.get(curr_node)
                if agent is None:
                    break

                # 1. Memory-assisted shortcut
                if target in agent.memory:
                    try:
                        curr_nbrs = set(G.neighbors(curr_node))
                    except Exception:
                        break

                    if target in curr_nbrs:
                        path.append(target)
                        found = True
                        break

                    # target is a friend-of-friend — find bridge
                    bridge = None
                    for nb in curr_nbrs:
                        try:
                            if target in G.neighbors(nb):
                                bridge = nb
                                break
                        except Exception:
                            continue

                    if bridge:
                        path.extend([bridge, target])
                        found = True
                    break

                # 2. Gradient-ascent fallback
                try:
                    neighbors = list(G.neighbors(curr_node))
                except Exception:
                    break

                valid_neighbors = [nb for nb in neighbors if nb not in path]
                if not valid_neighbors:
                    break

                next_node = max(valid_neighbors, key=lambda nb: G.degree(nb) if nb in G else 0)
                path.append(next_node)
                curr_node = next_node

                if curr_node == target:
                    found = True
                    break

            if found:
                success_count += 1
                total_hops    += len(path) - 1

        except Exception:
            # Per-query safety net — never crash the whole evaluation
            continue

    avg_hops     = total_hops / success_count if success_count > 0 else 0.0
    success_rate = (success_count / num_queries) * 100

    return round(avg_hops, 4), round(success_rate, 2)


# ===========================================================================
# CONFIG
# ===========================================================================
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'num_nodes':          state['num_nodes'],
        'initial_degree':     state['initial_degree'],
        'alpha':              runtime_config['alpha'],
        'beta':               runtime_config['beta'],
        'gamma':              runtime_config['gamma'],
        'query_ttl':          runtime_config['query_ttl'],
        'num_search_queries': runtime_config['num_search_queries'],
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.get_json(force=True) or {}

    # Graph topology params
    if 'num_nodes' in data:
        state['num_nodes'] = max(10, min(1000, int(data['num_nodes'])))
    if 'initial_degree' in data:
        state['initial_degree'] = max(2, min(20, int(data['initial_degree'])))

    # Utility function weights
    if 'alpha' in data:
        runtime_config['alpha'] = max(0.0, float(data['alpha']))
    if 'beta' in data:
        runtime_config['beta']  = max(0.0, float(data['beta']))
    if 'gamma' in data:
        runtime_config['gamma'] = max(0.0, float(data['gamma']))

    # Search params
    if 'query_ttl' in data:
        runtime_config['query_ttl']          = max(5, min(200, int(data['query_ttl'])))
    if 'num_search_queries' in data:
        runtime_config['num_search_queries'] = max(10, min(5000, int(data['num_search_queries'])))

    # If graph agents exist, propagate new alpha/beta/gamma into them
    if state['agents'] and any(k in data for k in ('alpha', 'beta', 'gamma')):
        _propagate_weights_to_agents()

    return jsonify({
        'status':         'success',
        'num_nodes':      state['num_nodes'],
        'initial_degree': state['initial_degree'],
        **runtime_config,
    })


def _propagate_weights_to_agents():
    """Monkey-patch agent utility via closure — avoids restarting simulation."""
    import math

    alpha = runtime_config['alpha']
    beta  = runtime_config['beta']
    gamma = runtime_config['gamma']
    G     = state['graph']

    for agent in state['agents'].values():
        def _make_utility(ag):
            def calculate_utility(target_id):
                target_degree = G.degree(target_id) if target_id in G else 0
                benefit       = alpha * math.log(1 + target_degree)
                my_degree     = G.degree(ag.id) if ag.id in G else 0
                cost          = beta * (my_degree / 10.0)
                my_neighbors     = set(G.neighbors(ag.id)) if ag.id in G else set()
                target_neighbors = set(G.neighbors(target_id)) if target_id in G else set()
                union_size       = len(my_neighbors | target_neighbors)
                similarity       = len(my_neighbors & target_neighbors) / union_size if union_size else 0.0
                return benefit - cost + gamma * similarity
            return calculate_utility
        agent.calculate_utility = _make_utility(agent)


# ===========================================================================
# GRAPH
# ===========================================================================
@app.route('/api/graph/initialize', methods=['POST'])
def api_initialize_graph():
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

        # Propagate current runtime weights into freshly created agents
        _propagate_weights_to_agents()

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
    G, err = _require_graph()
    if err:
        return err

    try:
        degree_dict = dict(G.degree())
        max_degree  = max(degree_dict.values()) if degree_dict else 1

        all_nodes  = list(G.nodes())
        sample     = all_nodes if len(all_nodes) <= 500 else random.sample(all_nodes, 500)
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
    G, err = _require_graph()
    if err:
        return err

    try:
        agents       = state['agents']
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
    return jsonify({
        'apl':        state['history']['apl'],
        'clustering': state['history']['clustering'],
        'steps':      len(state['history']['apl']),
    })


# ===========================================================================
# SEARCH
# ===========================================================================
@app.route('/api/search/baseline', methods=['POST'])
def search_baseline():
    G, err = _require_graph()
    if err:
        return err

    try:
        data  = request.get_json(force=True) or {}
        num_q = max(10, min(5000, int(data.get('num_queries', runtime_config['num_search_queries']))))
        ttl   = max(5,  min(200,  int(data.get('ttl',         runtime_config['query_ttl']))))

        avg_hops, success_rate = _test_routing_performance(G, state['agents'], num_q, ttl)
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
    G, err = _require_graph()
    if err:
        return err

    try:
        data  = request.get_json(force=True) or {}
        num_q = max(10, min(5000, int(data.get('num_queries', runtime_config['num_search_queries']))))
        ttl   = max(5,  min(200,  int(data.get('ttl',         runtime_config['query_ttl']))))

        avg_hops, success_rate = _test_routing_performance(G, state['agents'], num_q, ttl)
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
# STATUS
# ===========================================================================
@app.route('/api/status', methods=['GET'])
def get_status():
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
        **runtime_config,
    })


# ===========================================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
