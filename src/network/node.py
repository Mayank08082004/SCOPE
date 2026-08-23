import socket
import threading
import time
import os
import requests
import random
from src.network.protocol import send_message, receive_message
from src.agent import _jit_calculate_utility
from src.config import ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT

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
        
        # Register with tracker
        self.register_with_tracker()

    def register_with_tracker(self):
        try:
            payload = {
                "node_id": self.node_id,
                "ip": self.host,
                "port": self.port,
                "is_defector": self.is_defector
            }
            res = requests.post(f"{self.tracker_url}/api/tracker/register", json=payload)
            if res.status_code == 200:
                bootstrap = res.json().get("bootstrap", {})
                self.memory.update(bootstrap)
        except Exception as e:
            print(f"[{self.node_id}] Failed to register with tracker: {e}")

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
                    requests.post(f"{self.tracker_url}/api/tracker/telemetry", json={"packets_dropped": 1})
                else:
                    # Honest node: process successfully
                    pass
            
            elif msg_type == "CONTROL_SHUTDOWN":
                print(f"[{self.node_id}] Received C2 Kill Command. Terminating...")
                os._exit(1)
                
            elif msg_type == "CONTROL_TOGGLE_DEFECTOR":
                self.is_defector = not self.is_defector
                print(f"[{self.node_id}] Received C2 Toggle Defector. Now is_defector={self.is_defector}")
                
            elif msg_type == "CONTROL_START_TRANSFER":
                target_id = msg["target_id"]
                transfer_id = msg["transfer_id"]
                if target_id == self.node_id:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", json={
                        "transfer_id": transfer_id,
                        "status": "SUCCESS",
                        "path": [self.node_id],
                        "reason": "Arrived at Source (Loopback)"
                    })
                else:
                    self.route_file_transfer(target_id, transfer_id, [self.node_id], 20)
                
            elif msg_type == "FILE_TRANSFER":
                target_id = msg["target_id"]
                transfer_id = msg["transfer_id"]
                path = msg["path"]
                ttl = msg["ttl"]
                
                if self.is_defector:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", json={
                        "transfer_id": transfer_id,
                        "status": "DROPPED_BY_DEFECTOR",
                        "path": path + [self.node_id],
                        "reason": f"Dropped by Defector {self.node_id}"
                    })
                elif self.node_id == target_id:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", json={
                        "transfer_id": transfer_id,
                        "status": "SUCCESS",
                        "path": path + [self.node_id],
                        "reason": ""
                    })
                elif ttl <= 0:
                    requests.post(f"{self.tracker_url}/api/tracker/transfer_result", json={
                        "transfer_id": transfer_id,
                        "status": "FAILED_TTL",
                        "path": path + [self.node_id],
                        "reason": "TTL Expired"
                    })
                else:
                    self.route_file_transfer(target_id, transfer_id, path + [self.node_id], ttl)

        conn.close()

    def route_file_transfer(self, target_id, transfer_id, path, ttl):
        # Helper to safely send and report failure
        def safe_send(sock, msg_dict, attempt_node):
            if not send_message(sock, msg_dict):
                requests.post(f"{self.tracker_url}/api/tracker/transfer_result", json={
                    "transfer_id": transfer_id,
                    "status": "FAILED_SOCKET_CLOSED",
                    "path": path,
                    "reason": f"Socket closed when forwarding to {attempt_node}"
                })
                return False
            return True
            
        # 1. Memory-assisted shortcut
        if target_id in self.peers:
            msg = {"type": "FILE_TRANSFER", "target_id": target_id, "transfer_id": transfer_id, "path": path, "ttl": ttl - 1}
            safe_send(self.peers[target_id], msg, target_id)
            return
            
        if target_id in self.memory:
            bridge = next((n for n in self.peers if target_id in self.peer_neighbors.get(n, []) and n not in path), None)
            if bridge:
                msg = {"type": "FILE_TRANSFER", "target_id": target_id, "transfer_id": transfer_id, "path": path, "ttl": ttl - 1}
                safe_send(self.peers[bridge], msg, bridge)
                return
                
        # 2. Gradient-ascent fallback
        valid_neighbors = [n for n in self.peers if n not in path]
        if not valid_neighbors:
            requests.post(f"{self.tracker_url}/api/tracker/transfer_result", json={
                "transfer_id": transfer_id,
                "status": "FAILED_DEADEND",
                "path": path,
                "reason": f"Hit dead-end at {self.node_id}"
            })
            return
            
        next_node = max(valid_neighbors, key=lambda n: self.peer_degrees.get(n, 0))
        msg = {"type": "FILE_TRANSFER", "target_id": target_id, "transfer_id": transfer_id, "path": path, "ttl": ttl - 1}
        safe_send(self.peers[next_node], msg, next_node)

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

    def request_state_from_peers(self):
        for peer_id, sock in list(self.peers.items()):
            send_message(sock, {"type": "GET_DEGREE"})
            send_message(sock, {"type": "GET_NEIGHBORS"})

    def ooda_loop(self):
        """Physical implementation of the OODA loop."""
        while self.running:
            time.sleep(random.uniform(3, 6)) # Step every 3-6 seconds
            
            current_neighbors = list(self.peers.keys())
            
            # Heartbeat to tracker
            try:
                requests.post(f"{self.tracker_url}/api/tracker/heartbeat", json={
                    "node_id": self.node_id,
                    "connected_peers": current_neighbors
                }, timeout=2.0)
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
                
                # Betweenness is purely topological, tracker could calculate it but for real world we use local approx (0)
                u = _jit_calculate_utility(float(target_degree), 0.0, float(my_degree), float(union_size), float(intersection_size), float(ALPHA), float(BETA), float(GAMMA), float(BETWEENNESS_WEIGHT))
                
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
                # To evaluate a candidate, we must temporarily connect or assume. In a real network, we'd ping them.
                # For simplicity, we assume degree 1 and 0 intersection until we actually connect.
                u = _jit_calculate_utility(1.0, 0.0, float(my_degree), float(my_degree+1), 0.0, float(ALPHA), float(BETA), float(GAMMA), float(BETWEENNESS_WEIGHT))
                if u > best_u:
                    best_u = u
                    best_candidate = c

            if best_candidate and best_u > worst_u * 1.1:
                self.disconnect_peer(worst_neighbor)
                self.connect_to_peer(best_candidate, self.memory[best_candidate]["ip"], self.memory[best_candidate]["port"])

            # Send a data packet to test routing
            target_to_send = random.choice(current_neighbors)
            try:
                requests.post(f"{self.tracker_url}/api/tracker/telemetry", json={"packets_sent": 1})
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
