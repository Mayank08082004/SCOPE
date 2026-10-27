from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import logging
import threading
import os
import networkx as nx

# Disable Flask default logging for clean output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# C2 Authentication Token — must match node.py and docker-compose.yml
# ---------------------------------------------------------------------------
C2_AUTH_TOKEN = os.environ.get("C2_AUTH_TOKEN", "SCOPE_DEFAULT_C2_SECRET")

# --- Global State for the Tracker ---
# nodes: { "node_1": {"ip": "172.20.0.10", "port": 5000, "is_defector": False, "last_seen": timestamp} }
nodes = {}

# edges: { "node_1": ["node_2", "node_3"] }
edges = {}

# telemetry
telemetry = {
    "total_packets_sent": 0,
    "total_packets_dropped": 0
}

# ---------------------------------------------------------------------------
# Phase 4 — Distributed Betweenness Centrality
# Periodically recomputed from the edge topology reported by heartbeats.
# Normalized to [0.0, 1.0] as required by _jit_calculate_utility contract.
# ---------------------------------------------------------------------------
betweenness_scores = {}   # {node_id: float in [0.0, 1.0]}
_betweenness_lock = threading.Lock()

BETWEENNESS_RECOMPUTE_INTERVAL = 15  # seconds


def _recompute_betweenness():
    """
    Background thread: rebuild a NetworkX graph from the active edges dict
    and compute sampled betweenness centrality.  Results are normalized to
    the [0.0, 1.0] range as required by the _jit_calculate_utility contract
    (which internally multiplies by 100.0).
    """
    global betweenness_scores
    while True:
        time.sleep(BETWEENNESS_RECOMPUTE_INTERVAL)
        try:
            G = nx.Graph()
            # Add all known nodes
            for node_id in list(nodes.keys()):
                G.add_node(node_id)
            # Add edges from heartbeat data
            for src, neighbors in list(edges.items()):
                for dst in neighbors:
                    if dst in nodes:  # only add edges to live nodes
                        G.add_edge(src, dst)

            if G.number_of_nodes() < 2:
                continue

            # Sampled betweenness for performance (k = min(50, N))
            k = min(50, G.number_of_nodes())
            bc = nx.betweenness_centrality(G, k=k)

            # Normalize to [0.0, 1.0]
            max_bc = max(bc.values()) if bc else 1.0
            if max_bc > 0:
                normalized = {nid: round(val / max_bc, 6) for nid, val in bc.items()}
            else:
                normalized = {nid: 0.0 for nid in bc}

            with _betweenness_lock:
                betweenness_scores = normalized

        except Exception as e:
            print(f"[Tracker] Betweenness recomputation error: {e}")


# Start betweenness recomputation background thread
_bw_thread = threading.Thread(target=_recompute_betweenness, daemon=True)
_bw_thread.start()


@app.route('/api/tracker/register', methods=['POST'])
def register():
    """Nodes call this on startup to join the network."""
    data = request.json
    node_id = data.get('node_id')
    nodes[node_id] = {
        'ip': data.get('ip'),
        'port': data.get('port'),
        'is_defector': data.get('is_defector', False),
        'last_seen': time.time()
    }
    if node_id not in edges:
        edges[node_id] = []
        
    # Return a list of up to 10 random known nodes to help them bootstrap
    import random
    available_nodes = [n for n in nodes.keys() if n != node_id]
    bootstrap_nodes = random.sample(available_nodes, min(len(available_nodes), 10))
    bootstrap_addrs = {n: {"ip": nodes[n]["ip"], "port": nodes[n]["port"]} for n in bootstrap_nodes}
    
    return jsonify({"status": "registered", "bootstrap": bootstrap_addrs})


@app.route('/api/tracker/heartbeat', methods=['POST'])
def heartbeat():
    """
    Nodes call this periodically to update their active connections.
    Phase 4: response now includes betweenness centrality scores for
    the node and its connected peers (normalized to [0.0, 1.0]).
    """
    data = request.json
    node_id = data.get('node_id')
    
    if node_id in nodes:
        nodes[node_id]['last_seen'] = time.time()
        edges[node_id] = data.get('connected_peers', [])

        # Phase 4: return betweenness scores for this node + its peers
        connected = data.get('connected_peers', [])
        relevant_nodes = [node_id] + connected

        with _betweenness_lock:
            bw_subset = {
                nid: betweenness_scores.get(nid, 0.0)
                for nid in relevant_nodes
            }

        return jsonify({
            "status": "ok",
            "betweenness": bw_subset
        })
    return jsonify({"status": "not_found"}), 404


@app.route('/api/tracker/telemetry', methods=['POST'])
def update_telemetry():
    """Nodes report when they send or drop packets."""
    data = request.json
    telemetry["total_packets_sent"] += data.get("packets_sent", 0)
    telemetry["total_packets_dropped"] += data.get("packets_dropped", 0)
    return jsonify({"status": "ok"})


@app.route('/api/tracker/control', methods=['POST'])
def control_node():
    """
    C2 Endpoint: Relays commands from frontend to target physical node.
    Phase 4: Hardened with authorization token validation.
    """
    # -----------------------------------------------------------------
    # Phase 4 — Auth token validation
    # -----------------------------------------------------------------
    auth_token = request.headers.get('X-C2-Auth-Token', '')
    if auth_token != C2_AUTH_TOKEN:
        return jsonify({
            "status": "error",
            "message": "Forbidden — invalid or missing C2 auth token"
        }), 403

    data = request.json
    node_id = data.get('node_id')
    action = data.get('action') # 'KILL', 'TOGGLE_DEFECTOR', or 'CURE_DEFECTOR'
    
    if node_id not in nodes:
        return jsonify({"status": "error", "message": "Node not found"}), 404
        
    target_ip = nodes[node_id]['ip']
    target_port = nodes[node_id]['port']
    
    from src.network.protocol import send_message
    import socket
    
    action_map = {
        'KILL': 'CONTROL_SHUTDOWN',
        'TOGGLE_DEFECTOR': 'CONTROL_TOGGLE_DEFECTOR',
        'CURE_DEFECTOR': 'CONTROL_CURE_DEFECTOR',
    }
    msg_type = action_map.get(action)
    if not msg_type:
        return jsonify({"status": "error", "message": f"Unknown action: {action}"}), 400
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((target_ip, target_port))
        send_message(sock, {
            "type": msg_type,
            "auth_token": C2_AUTH_TOKEN   # Phase 4: pass token to node
        })
        sock.close()
        
        # Immediate local state update for faster UI reflection
        if action == 'TOGGLE_DEFECTOR':
            nodes[node_id]['is_defector'] = not nodes[node_id]['is_defector']
        elif action == 'CURE_DEFECTOR':
            nodes[node_id]['is_defector'] = False
        elif action == 'KILL':
            del nodes[node_id]
            if node_id in edges: del edges[node_id]
            
        return jsonify({"status": "success", "action": action})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

transfers = {}

@app.route('/api/tracker/transfer', methods=['POST'])
def start_transfer():
    """Starts a file transfer simulation from source to target."""
    data = request.json
    source_id = data.get('source_id')
    target_id = data.get('target_id')
    
    import uuid
    transfer_id = str(uuid.uuid4())
    transfers[transfer_id] = {
        "status": "IN_PROGRESS",
        "path": [],
        "backtracks": [],     # Phase 4: backtrack tracking
        "reason": ""
    }
    
    if source_id not in nodes or target_id not in nodes:
        transfers[transfer_id] = {
            "status": "FAILED",
            "path": [],
            "backtracks": [],
            "reason": "Invalid nodes"
        }
        return jsonify({"transfer_id": transfer_id})
        
    target_ip = nodes[source_id]['ip']
    target_port = nodes[source_id]['port']
    
    from src.network.protocol import send_message
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((target_ip, target_port))
        send_message(sock, {
            "type": "CONTROL_START_TRANSFER",
            "target_id": target_id,
            "transfer_id": transfer_id
        })
        sock.close()
    except Exception as e:
        transfers[transfer_id] = {
            "status": "FAILED",
            "path": [],
            "backtracks": [],
            "reason": str(e)
        }
        
    return jsonify({"transfer_id": transfer_id})

@app.route('/api/tracker/transfer_result', methods=['POST'])
def transfer_result():
    """
    Nodes report the result of a file transfer here.
    Phase 4: now includes 'backtracks' array for animation support.
    """
    data = request.json
    transfer_id = data.get('transfer_id')
    if transfer_id in transfers:
        transfers[transfer_id] = {
            "status": data.get('status'),
            "path": data.get('path', []),
            "backtracks": data.get('backtracks', []),   # Phase 4
            "reason": data.get('reason', "")
        }
    return jsonify({"status": "ok"})

@app.route('/api/tracker/transfer_status/<transfer_id>', methods=['GET'])
def get_transfer_status(transfer_id):
    """
    Frontend polls this to get transfer results.
    Phase 4 schema:
    {
        "status": "SUCCESS",
        "path": ["node_1", "node_14", "node_42", "node_60"],
        "backtracks": [["node_14", "node_22"]]
    }
    """
    if transfer_id in transfers:
        return jsonify(transfers[transfer_id])
    return jsonify({"status": "NOT_FOUND"}), 404

# --- Frontend API Routes ---
@app.route('/api/network/state', methods=['GET'])
def get_network_state():
    """Used by the React frontend (/network page) to visualize the physical topology."""
    # Clean up dead nodes (no heartbeat in 30s)
    current_time = time.time()
    dead_nodes = [n for n, data in nodes.items() if current_time - data['last_seen'] > 30]
    for dead in dead_nodes:
        del nodes[dead]
        if dead in edges:
            del edges[dead]

    # Phase 4: include betweenness scores in state response
    with _betweenness_lock:
        bw_copy = dict(betweenness_scores)

    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "telemetry": telemetry,
        "betweenness": bw_copy
    })

# ---------------------------------------------------------------------------
# Phase 4 — Betweenness Centrality API (for debugging / monitoring)
# ---------------------------------------------------------------------------
@app.route('/api/tracker/betweenness', methods=['GET'])
def get_betweenness():
    """Returns current betweenness centrality scores for all nodes."""
    with _betweenness_lock:
        return jsonify({
            "betweenness": dict(betweenness_scores),
            "num_nodes": len(betweenness_scores),
            "last_computed": "periodic (every 15s)"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
