import socket
import threading
import time
import os
import requests

_orig_post = requests.post
def safe_post(*args, **kwargs):
    kwargs.setdefault('timeout', 2.0)
    try:
        return _orig_post(*args, **kwargs)
    except Exception as e:
        class DummyResponse:
            status_code = 500
            def json(self): return {}
        return DummyResponse()
requests.post = safe_post

import random
from src.network.protocol import send_message, receive_message
from src.agent import _jit_calculate_utility
from src.config import ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT, HYSTERESIS_EPSILON

# ---------------------------------------------------------------------------
# C2 Authentication Token — prevents arbitrary TCP sockets from terminating
# nodes. Must match the token configured in tracker.py and docker-compose.yml.
# ---------------------------------------------------------------------------
C2_AUTH_TOKEN = os.environ.get("C2_AUTH_TOKEN", "SCOPE_DEFAULT_C2_SECRET")

# ---------------------------------------------------------------------------
# Defector Quarantine Thresholds
# ---------------------------------------------------------------------------
SUSPICIOUS_THRESHOLD = 3       # unacked transfers before flagging peer
ACK_TIMEOUT_SECONDS  = 10.0   # seconds to wait for a TRANSFER_ACK


class Node:
    def __init__(self, node_id, host, port, tracker_url, is_defector=False):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.tracker_url = tracker_url
        self.is_defector = is_defector
        
        # Connections: {node_id: socket_object}
        self.peers = {}
        # Known nodes: {node_id: {"ip": ip, "port": port}}
        self.memory = {}
        
        # Async state for OODA evaluation
        self.peer_degrees = {}
        self.peer_neighbors = {}

        # -----------------------------------------------------------------
        # Phase 4 — Betweenness Centrality (fed from tracker heartbeat)
        # -----------------------------------------------------------------
        self.peer_betweenness = {}   # {peer_id: float in [0.0, 1.0]}
        self.my_betweenness = 0.0    # own normalized betweenness score

        # -----------------------------------------------------------------
        # Phase 4 — Proof-of-Throughput: delivery tracking per peer
        # -----------------------------------------------------------------
        self.peer_delivery_stats = {}   # {peer_id: {"sent": int, "acked": int}}
        self.suspicious_peers = set()   # peers flagged for packet drops

        # -----------------------------------------------------------------
        # Phase 4 — ACK-based defector detection
        # pending_acks: {transfer_id: {"peer": peer_id, "timestamp": float}}
        # -----------------------------------------------------------------
        self.pending_acks = {}

        # Start server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        
        self.running = True
        self.server_thread = threading.Thread(target=self.accept_connections)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.ooda_thread = threading.Thread(target=self.ooda_loop)
        self.ooda_thread.daemon = True
        self.ooda_thread.start()

        # Background thread to timeout unacknowledged transfers
        self.ack_monitor_thread = threading.Thread(target=self._monitor_pending_acks)
        self.ack_monitor_thread.daemon = True
        self.ack_monitor_thread.start()
        
        # Register with tracker
        self.register_with_tracker()

    # =====================================================================
    # PEER DELIVERY SUCCESS RATE  (T_ij ∈ [0.0, 1.0])
    # =====================================================================
    def get_peer_throughput(self, peer_id):
        """
        Returns the delivery success rate for a peer.
        Suspicious peers → T_ij = 0.001  (Theorem 7.1 isolation).
        Unknown peers → T_ij = 1.0      (optimistic default).
        """
        if peer_id in self.suspicious_peers:
            return 0.001
        stats = self.peer_delivery_stats.get(peer_id)
        if stats and stats["sent"] > 0:
            return max(0.001, stats["acked"] / stats["sent"])
        return 1.0   # no data yet → optimistic

    def _record_send(self, peer_id, transfer_id):
        """Record that we routed a transfer through this peer."""
        if peer_id not in self.peer_delivery_stats:
            self.peer_delivery_stats[peer_id] = {"sent": 0, "acked": 0}
        self.peer_delivery_stats[peer_id]["sent"] += 1
        self.pending_acks[transfer_id] = {
            "peer": peer_id,
            "timestamp": time.time()
        }

    def _record_ack(self, transfer_id):
        """Record a successful ACK for a transfer."""
        pending = self.pending_acks.pop(transfer_id, None)
        if pending:
            peer_id = pending["peer"]
            if peer_id in self.peer_delivery_stats:
                self.peer_delivery_stats[peer_id]["acked"] += 1
            # If peer was suspicious and now acknowledging, consider rehabilitating
            if peer_id in self.suspicious_peers:
                stats = self.peer_delivery_stats.get(peer_id, {"sent": 1, "acked": 1})
                if stats["sent"] > 0 and (stats["acked"] / stats["sent"]) > 0.5:
                    self.suspicious_peers.discard(peer_id)

    def _monitor_pending_acks(self):
        """Background thread: flag peers with timed-out ACKs as suspicious."""
        while self.running:
            time.sleep(5.0)
            now = time.time()
            expired = []
            for tid, info in list(self.pending_acks.items()):
                if now - info["timestamp"] > ACK_TIMEOUT_SECONDS:
                    expired.append(tid)
            for tid in expired:
                info = self.pending_acks.pop(tid, None)
                if info:
                    peer_id = info["peer"]
                    stats = self.peer_delivery_stats.get(peer_id, {"sent": 0, "acked": 0})
                    unacked = stats["sent"] - stats["acked"]
                    if unacked >= SUSPICIOUS_THRESHOLD:
                        self.suspicious_peers.add(peer_id)
                        print(f"[{self.node_id}] ⚠️ Peer {peer_id} flagged as SUSPICIOUS ({unacked} unacked transfers)")

    # =====================================================================
    # REGISTRATION
    # =====================================================================
    def register_with_tracker(self):
        try:
            payload = {
                "node_id": self.node_id,
                "ip": self.host,
                "port": self.port,
                "is_defector": self.is_defector
            }
            res = requests.post(f"{self.tracker_url}/api/tracker/register", json=payload, timeout=5.0)
            if res.status_code == 200:
                bootstrap = res.json().get("bootstrap", {})
                self.memory.update(bootstrap)
        except Exception as e:
            print(f"[{self.node_id}] Failed to register with tracker: {e}")

    # =====================================================================
    # CONNECTION HANDLING
    # =====================================================================
    def accept_connections(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                pass

    def handle_client(self, conn):
        """Handle incoming messages from peers."""
        while self.running:
            msg = receive_message(conn)
            if not msg:
                break
                
            msg_type = msg.get("type")
            
            if msg_type == "HANDSHAKE":
                peer_id = msg["node_id"]
                self.peers[peer_id] = conn
                self.memory[peer_id] = {"ip": msg["ip"], "port": msg["port"]}
                
            elif msg_type == "GET_DEGREE":
                degree = len(self.peers)
                if self.is_defector:
                    degree = degree * 3 + 5 # Defectors lie to look attractive
                send_message(conn, {"type": "DEGREE_RES", "peer_id": self.node_id, "degree": degree})
                
            elif msg_type == "GET_NEIGHBORS":
                send_message(conn, {"type": "NEIGHBORS_RES", "peer_id": self.node_id, "neighbors": list(self.peers.keys())})
                
            elif msg_type == "DEGREE_RES":
                pid = msg.get("peer_id")
                if pid: self.peer_degrees[pid] = msg.get("degree", 0)
                
            elif msg_type == "NEIGHBORS_RES":
                pid = msg.get("peer_id")
                if pid: self.peer_neighbors[pid] = msg.get("neighbors", [])
                
            elif msg_type == "DATA_PACKET":
                if self.is_defector:
                    # Black Hole attack: silent drop
                    requests.post(f"{self.tracker_url}/api/tracker/telemetry", json={"packets_dropped": 1}, timeout=2.0)
                else:
                    # Honest node: process successfully
                    pass

            # -----------------------------------------------------------------
            # Phase 4 — TRANSFER_ACK: destination confirms receipt
            # -----------------------------------------------------------------
            elif msg_type == "TRANSFER_ACK":
                transfer_id = msg.get("transfer_id")
                if transfer_id:
                    self._record_ack(transfer_id)
            
            # -----------------------------------------------------------------
            # Phase 4 — BACKTRACK: dead-end node asks previous hop to try
            # the next-best neighbor
            # -----------------------------------------------------------------
            elif msg_type == "BACKTRACK":
                target_id = msg["target_id"]
                transfer_id = msg["transfer_id"]
                path = msg["path"]
                ttl = msg["ttl"]
                attempted = set(msg.get("attempted", []))
                backtracks = msg.get("backtracks", [])
                # Try next best neighbor excluding already-attempted ones
                self.route_file_transfer(
                    target_id, transfer_id, path, ttl,
                    attempted=attempted, backtracks=backtracks
                )

            # -----------------------------------------------------------------
            # C2 Commands — Phase 4 hardened with auth token validation
            # -----------------------------------------------------------------
            elif msg_type == "CONTROL_SHUTDOWN":
                token = msg.get("auth_token", "")
                if token != C2_AUTH_TOKEN:
                    print(f"[{self.node_id}] ❌ Rejected KILL command — invalid auth token")
                    continue
                print(f"[{self.node_id}] Received C2 Kill Command. Terminating...")
                os._exit(1)
                
            elif msg_type == "CONTROL_TOGGLE_DEFECTOR":
                token = msg.get("auth_token", "")
                if token != C2_AUTH_TOKEN:
                    print(f"[{self.node_id}] ❌ Rejected TOGGLE_DEFECTOR command — invalid auth token")
                    continue
                self.is_defector = not self.is_defector
                print(f"[{self.node_id}] Received C2 Toggle Defector. Now is_defector={self.is_defector}")

            # -----------------------------------------------------------------
            # Phase 4 — CONTROL_CURE_DEFECTOR: rehabilitate a defector
            # -----------------------------------------------------------------
            elif msg_type == "CONTROL_CURE_DEFECTOR":
                token = msg.get("auth_token", "")
                if token != C2_AUTH_TOKEN:
                    print(f"[{self.node_id}] ❌ Rejected CURE command — invalid auth token")
                    continue
                self.is_defector = False
                self.suspicious_peers.clear()
                print(f"[{self.node_id}] Received C2 Cure Command. Defector status cleared.")
                
            elif msg_type == "CONTROL_START_TRANSFER":
                target_id = msg["target_id"]
                transfer_id = msg["transfer_id"]
                if target_id == self.node_id:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", timeout=2.0, json={
                        "transfer_id": transfer_id,
                        "status": "SUCCESS",
                        "path": [self.node_id],
                        "backtracks": [],
                        "reason": "Arrived at Source (Loopback)"
                    })
                else:
                    self.route_file_transfer(target_id, transfer_id, [self.node_id], 20)
                
            elif msg_type == "FILE_TRANSFER":
                target_id = msg["target_id"]
                transfer_id = msg["transfer_id"]
                path = msg["path"]
                ttl = msg["ttl"]
                attempted = set(msg.get("attempted", []))
                backtracks = msg.get("backtracks", [])
                
                if self.is_defector:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", timeout=2.0, json={
                        "transfer_id": transfer_id,
                        "status": "DROPPED_BY_DEFECTOR",
                        "path": path + [self.node_id],
                        "backtracks": backtracks,
                        "reason": f"Dropped by Defector {self.node_id}"
                    })
                elif self.node_id == target_id:
                    # Success! Send ACK back to source (first node in path)
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", timeout=2.0, json={
                        "transfer_id": transfer_id,
                        "status": "SUCCESS",
                        "path": path + [self.node_id],
                        "backtracks": backtracks,
                        "reason": ""
                    })
                    # Send TRANSFER_ACK to the node that forwarded to us
                    if len(path) >= 1:
                        sender_id = path[-1]
                        if sender_id in self.peers:
                            send_message(self.peers[sender_id], {
                                "type": "TRANSFER_ACK",
                                "transfer_id": transfer_id,
                                "acked_by": self.node_id
                            })
                elif ttl <= 0:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", timeout=2.0, json={
                        "transfer_id": transfer_id,
                        "status": "FAILED_TTL",
                        "path": path + [self.node_id],
                        "backtracks": backtracks,
                        "reason": "TTL Expired"
                    })
                else:
                    self.route_file_transfer(
                        target_id, transfer_id, path + [self.node_id], ttl,
                        attempted=attempted, backtracks=backtracks
                    )

        conn.close()

    # =====================================================================
    # ROUTING — Phase 4 Backtracking State Machine
    # =====================================================================
    def route_file_transfer(self, target_id, transfer_id, path, ttl,
                            attempted=None, backtracks=None):
        """
        Memory-assisted gradient-ascent routing with backtracking.

        When a packet hits a dead-end (all neighbors visited/attempted),
        instead of immediately failing with FAILED_DEADEND, we send a
        BACKTRACK signal to the previous hop to try the next-best-degree
        neighbor — eliminating the dead-end failure mode.
        """
        if attempted is None:
            attempted = set()
        if backtracks is None:
            backtracks = []

        # Helper to safely send and report failure
        def safe_send(sock, msg_dict, attempt_node):
            if not send_message(sock, msg_dict):
                requests.post(f"{self.tracker_url}/api/tracker/transfer_result", timeout=2.0, json={
                    "transfer_id": transfer_id,
                    "status": "FAILED_SOCKET_CLOSED",
                    "path": path,
                    "backtracks": backtracks,
                    "reason": f"Socket closed when forwarding to {attempt_node}"
                })
                return False
            return True
            
        # 1. Memory-assisted shortcut
        if target_id in self.peers:
            self._record_send(target_id, transfer_id)
            msg = {
                "type": "FILE_TRANSFER",
                "target_id": target_id,
                "transfer_id": transfer_id,
                "path": path,
                "ttl": ttl - 1,
                "attempted": list(attempted),
                "backtracks": backtracks,
            }
            safe_send(self.peers[target_id], msg, target_id)
            return
            
        if target_id in self.memory:
            bridge = next(
                (n for n in self.peers
                 if target_id in self.peer_neighbors.get(n, [])
                 and n not in path and n not in attempted),
                None
            )
            if bridge:
                self._record_send(bridge, transfer_id)
                msg = {
                    "type": "FILE_TRANSFER",
                    "target_id": target_id,
                    "transfer_id": transfer_id,
                    "path": path,
                    "ttl": ttl - 1,
                    "attempted": list(attempted),
                    "backtracks": backtracks,
                }
                safe_send(self.peers[bridge], msg, bridge)
                return
                
        # 2. Gradient-ascent with backtracking support
        valid_neighbors = [
            n for n in self.peers
            if n not in path and n not in attempted
        ]

        if not valid_neighbors:
            # ---------------------------------------------------------------
            # BACKTRACKING: instead of failing, send BACKTRACK to previous hop
            # ---------------------------------------------------------------
            if len(path) >= 2:
                prev_hop = path[-2]
                if prev_hop in self.peers:
                    # Add current node to attempted set so prev_hop skips it
                    new_attempted = attempted | {self.node_id}
                    new_backtracks = backtracks + [[prev_hop, self.node_id]]
                    backtrack_msg = {
                        "type": "BACKTRACK",
                        "target_id": target_id,
                        "transfer_id": transfer_id,
                        "path": path[:-1],  # rewind path to exclude dead-end
                        "ttl": ttl,
                        "attempted": list(new_attempted),
                        "backtracks": new_backtracks,
                    }
                    send_message(self.peers[prev_hop], backtrack_msg)
                    return

            # Truly exhausted all options — no previous hop to backtrack to
            requests.post(f"{self.tracker_url}/api/tracker/transfer_result", timeout=2.0, json={
                "transfer_id": transfer_id,
                "status": "FAILED_DEADEND",
                "path": path,
                "backtracks": backtracks,
                "reason": f"Hit dead-end at {self.node_id} (backtracking exhausted)"
            })
            return
            
        # Pick the highest-degree unvisited, unattempted neighbor
        next_node = max(valid_neighbors, key=lambda n: self.peer_degrees.get(n, 0))
        self._record_send(next_node, transfer_id)
        msg = {
            "type": "FILE_TRANSFER",
            "target_id": target_id,
            "transfer_id": transfer_id,
            "path": path,
            "ttl": ttl - 1,
            "attempted": list(attempted),
            "backtracks": backtracks,
        }
        safe_send(self.peers[next_node], msg, next_node)

    # =====================================================================
    # PEER CONNECTION MANAGEMENT
    # =====================================================================
    def connect_to_peer(self, peer_id, ip, port):
        if peer_id == self.node_id or peer_id in self.peers:
            return
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((ip, port))
            
            # Send handshake
            send_message(sock, {
                "type": "HANDSHAKE", 
                "node_id": self.node_id,
                "ip": self.host,
                "port": self.port
            })
            
            sock.settimeout(None)
            self.peers[peer_id] = sock
            threading.Thread(target=self.handle_client, args=(sock,), daemon=True).start()
        except Exception:
            self.memory.pop(peer_id, None)

    def disconnect_peer(self, peer_id):
        if peer_id in self.peers:
            try:
                self.peers[peer_id].close()
            except Exception:
                pass
            del self.peers[peer_id]
            self.peer_degrees.pop(peer_id, None)
            self.peer_neighbors.pop(peer_id, None)
            self.peer_betweenness.pop(peer_id, None)

    def request_state_from_peers(self):
        for peer_id, sock in list(self.peers.items()):
            send_message(sock, {"type": "GET_DEGREE"})
            send_message(sock, {"type": "GET_NEIGHBORS"})

    # =====================================================================
    # OODA LOOP — Phase 4 upgraded with betweenness + δ throughput
    # =====================================================================
    def ooda_loop(self):
        """Physical implementation of the OODA loop."""
        while self.running:
            time.sleep(random.uniform(3, 6)) # Step every 3-6 seconds
            
            current_neighbors = list(self.peers.keys())
            
            # Heartbeat to tracker — Phase 4: receive betweenness scores
            try:
                res = requests.post(f"{self.tracker_url}/api/tracker/heartbeat", json={
                    "node_id": self.node_id,
                    "connected_peers": current_neighbors
                }, timeout=2.0)
                if res.status_code == 200:
                    data = res.json()
                    # Phase 4: read betweenness scores from tracker response
                    betweenness_data = data.get("betweenness", {})
                    if betweenness_data:
                        self.my_betweenness = betweenness_data.get(self.node_id, 0.0)
                        for pid, bw in betweenness_data.items():
                            self.peer_betweenness[pid] = bw
            except: pass
            
            if not current_neighbors:
                # If isolated, try to connect to a random known node
                if self.memory:
                    target = random.choice(list(self.memory.keys()))
                    self.connect_to_peer(target, self.memory[target]["ip"], self.memory[target]["port"])
                continue

            # Send async requests to update our knowledge
            self.request_state_from_peers()

            # Evaluate utility of current neighbors using cached state
            my_degree = len(current_neighbors)
            my_neighbors_set = set(current_neighbors)
            
            worst_neighbor = None
            worst_u = float('inf')
            
            for n in current_neighbors:
                target_degree = self.peer_degrees.get(n, 1)
                target_neighbors = set(self.peer_neighbors.get(n, []))
                
                union_size = len(my_neighbors_set | target_neighbors)
                intersection_size = len(my_neighbors_set & target_neighbors)
                
                # Phase 4: use real betweenness from tracker (normalized [0,1])
                target_betweenness = self.peer_betweenness.get(n, 0.0)
                # Phase 4: use measured peer throughput
                peer_throughput = self.get_peer_throughput(n)

                u = _jit_calculate_utility(
                    float(target_degree),
                    float(target_betweenness),
                    float(my_degree),
                    float(union_size),
                    float(intersection_size),
                    float(ALPHA),
                    float(BETA),
                    float(GAMMA),
                    float(BETWEENNESS_WEIGHT),
                    float(DELTA_WEIGHT),
                    float(peer_throughput)
                )
                
                if u < worst_u:
                    worst_u = u
                    worst_neighbor = n

            # Evaluate candidates
            candidates = list(set(self.memory.keys()) - set(current_neighbors) - {self.node_id})
            if not candidates:
                continue
                
            sample_candidates = random.sample(candidates, min(len(candidates), 3))
            
            best_candidate = None
            best_u = -float('inf')
            
            for c in sample_candidates:
                # Phase 4: use betweenness + throughput for candidate evaluation too
                candidate_betweenness = self.peer_betweenness.get(c, 0.0)
                candidate_throughput = self.get_peer_throughput(c)

                u = _jit_calculate_utility(
                    1.0,
                    float(candidate_betweenness),
                    float(my_degree),
                    float(my_degree + 1),
                    0.0,
                    float(ALPHA),
                    float(BETA),
                    float(GAMMA),
                    float(BETWEENNESS_WEIGHT),
                    float(DELTA_WEIGHT),
                    float(candidate_throughput)
                )
                if u > best_u:
                    best_u = u
                    best_candidate = c

            if best_candidate and (best_u - worst_u) > HYSTERESIS_EPSILON * max(0.01, abs(worst_u)):
                self.disconnect_peer(worst_neighbor)
                self.connect_to_peer(best_candidate, self.memory[best_candidate]["ip"], self.memory[best_candidate]["port"])

            # Send a data packet to test routing
            target_to_send = random.choice(current_neighbors)
            try:
                requests.post(f"{self.tracker_url}/api/tracker/telemetry", json={"packets_sent": 1}, timeout=2.0)
                send_message(self.peers[target_to_send], {"type": "DATA_PACKET"})
            except: pass

if __name__ == "__main__":
    ADJECTIVES = ["Quantum", "Cyber", "Neon", "Void", "Solar", "Lunar", "Stellar", "Cosmic", "Astro", "Nova", "Pulse"]
    NOUNS = ["Core", "Nexus", "Forge", "Grid", "Link", "Node", "Vault", "Spire", "Gate", "Hub"]
    generated_name = f"{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}-{random.randint(10,99)}"
    
    node_id = os.environ.get("NODE_ID", generated_name)
    host = "0.0.0.0"
    advertised_ip = socket.gethostbyname(socket.gethostname())
    port = int(os.environ.get("PORT", 5000))
    tracker = os.environ.get("TRACKER_URL", "http://tracker:5002")
    is_def = os.environ.get("IS_DEFECTOR", "False").lower() == "true"
    
    node = Node(node_id, advertised_ip, port, tracker, is_defector=is_def)
    print(f"[{node_id}] Started physical node (Defector={is_def}) on {advertised_ip}:{port}")
    
    # Keep main thread alive
    while True:
        time.sleep(10)
