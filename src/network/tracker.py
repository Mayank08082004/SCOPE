from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import logging

# Disable Flask default logging for clean output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

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
    """Nodes call this periodically to update their active connections."""
    data = request.json
    node_id = data.get('node_id')
    
    if node_id in nodes:
        nodes[node_id]['last_seen'] = time.time()
        edges[node_id] = data.get('connected_peers', [])
        return jsonify({"status": "ok"})
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
    """C2 Endpoint: Relays commands from frontend to target physical node."""
    data = request.json
    node_id = data.get('node_id')
    action = data.get('action') # 'KILL' or 'TOGGLE_DEFECTOR'
    
    if node_id not in nodes:
        return jsonify({"status": "error", "message": "Node not found"}), 404
        
    target_ip = nodes[node_id]['ip']
    target_port = nodes[node_id]['port']
    
    from src.network.protocol import send_message
    import socket
    
    msg_type = "CONTROL_SHUTDOWN" if action == 'KILL' else "CONTROL_TOGGLE_DEFECTOR"
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((target_ip, target_port))
        send_message(sock, {"type": msg_type})
        sock.close()
        
        # Immediate local state update for faster UI reflection
        if action == 'TOGGLE_DEFECTOR':
            nodes[node_id]['is_defector'] = not nodes[node_id]['is_defector']
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
    transfers[transfer_id] = {"status": "IN_PROGRESS", "path": [], "reason": ""}
    
    if source_id not in nodes or target_id not in nodes:
        transfers[transfer_id] = {"status": "FAILED", "path": [], "reason": "Invalid nodes"}
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
        transfers[transfer_id] = {"status": "FAILED", "path": [], "reason": str(e)}
        
    return jsonify({"transfer_id": transfer_id})

@app.route('/api/tracker/transfer_result', methods=['POST'])
def transfer_result():
    """Nodes report the result of a file transfer here."""
    data = request.json
    transfer_id = data.get('transfer_id')
    if transfer_id in transfers:
        transfers[transfer_id] = {
            "status": data.get('status'),
            "path": data.get('path', []),
            "reason": data.get('reason', "")
        }
    return jsonify({"status": "ok"})

@app.route('/api/tracker/transfer_status/<transfer_id>', methods=['GET'])
def get_transfer_status(transfer_id):
    """Frontend polls this to get transfer results."""
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
        del edges[dead]
        
    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "telemetry": telemetry
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
