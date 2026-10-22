# SCOPE: Physical Emulation Engine (Phase 3 Swarm)

Welcome to the **Physical Emulation Engine** of SCOPE. This subsystem transitions the theoretical and mathematical graph models from Phase 1 & 2 into real-world distributed systems engineering running on **isolated Docker containers** communicating via **raw TCP sockets**.

---

## 📌 Subsystem Architecture

The physical engine deploys up to 75+ containerized peer nodes communicating directly with one another over an isolated Docker bridge network (`scope_net`). A central lightweight Command & Control (C2) Tracker manages bootstrap registration and telemetry for the live React dashboard.

```
                               ┌─────────────────────────────┐
                               │   React C2 Dashboard (UI)   │
                               │   (http://localhost:5173)   │
                               └──────────────┬──────────────┘
                                              │ HTTP Polling / C2 Commands
                                              ▼
                               ┌─────────────────────────────┐
                               │     src/network/tracker.py  │
                               │  (Bootstrap DNS & C2 Server) │
                               │        (Port: 5002)         │
                               └──────────────┬──────────────┘
                                              │ Node Registration & Heartbeats
             ┌────────────────────────────────┴────────────────────────────────┐
             │                                                                 │
             ▼                                                                 ▼
 ┌───────────────────────┐                                         ┌───────────────────────┐
 │  src/network/node.py  │       Raw Localhost TCP Sockets         │  src/network/node.py  │
 │ (Container: node_1)   │◄───────────────────────────────────────►│ (Container: node_2)   │
 │ - Port: 5000          │        (Custom Binary JSON Framing)     │ - Port: 5000          │
 │ - Honest Peer         │                                         │ - Defector (Sybil)    │
 └───────────────────────┘                                         └───────────────────────┘
```

---

## 📂 Source Code Breakdown

### 1. `src/network/node.py` — The Containerized Peer
Each instance of `node.py` runs inside an isolated container with its own private IP address and loopback interface:

*   **Multi-Threaded Concurrency Model:**
    *   **Main Thread:** Initializes state, registers the container's physical IP with the Tracker, and monitors health.
    *   **TCP Server Accept Thread:** Listens continuously on port 5000 for incoming connections from peer containers.
    *   **OODA Loop Thread:** Wakes up every 3–6 seconds (randomized jitter to prevent thundering herd) to sample peers, calculate utility, and rewire connections.
    *   **Spawned Client Daemon Threads:** For every inbound or outbound TCP connection, a dedicated daemon thread is spawned to handle streaming socket reads. This ensures **Full-Duplex asynchronous I/O** without socket deadlocks.
*   **Routing Logic (Memory-Assisted Gradient Ascent):**
    *   When routing a `DATA_PACKET`, the node checks if the target IP is in its immediate neighbor table.
    *   If not, it queries neighboring nodes for their degrees via TCP and forwards to the highest-degree neighbor not already visited in the packet's `path` trace.
    *   `self.memory` tracks visited nodes to bypass the **Dead-End Phenomenon** (getting trapped in local clusters of super-hubs).
*   **Defector Mode (Adversarial Sybil Node):**
    *   Defectors report an artificially inflated degree (`actual_degree * 3 + 5`) in response to TCP degree queries.
    *   Honest nodes eagerly wire to defectors due to the $\alpha$ utility benefit.
    *   Upon receiving a `DATA_PACKET`, the defector silently drops it, acting as a **Black Hole** and reporting dropped telemetry to the Tracker.
*   **Game-Theoretic Utility Integration (Member 2 Hand-off):**
    *   `node.py` computes connection utility via `_jit_calculate_utility` in [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py).
    *   **Phase 4 Upgrade:** `_jit_calculate_utility` now accepts `delta=0.0` and `throughput=0.0` as optional parameters (backward-compatible).
    *   To activate Proof-of-Throughput defector defense, import `DELTA_WEIGHT` from [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py) and pass the peer's delivery success rate ($T_{ij} \in [0.0, 1.0]$) to `_jit_calculate_utility`. Defectors with zero throughput will be mathematically penalized and disconnected.
    *   Betweenness centrality is multiplied by `100.0` inside `_jit_calculate_utility`; `tracker.py` must provide normalized scores in $[0.0, 1.0]$.

---

### 2. `src/network/protocol.py` — Custom Binary-Prefixed TCP Framing
Raw TCP sockets provide a continuous byte stream without built-in message boundaries. `protocol.py` provides deterministic packet framing:

*   **Framing Mechanism:**
    *   Every message begins with a **4-byte big-endian unsigned integer** (`!I`) representing the byte-length of the following JSON payload.
    *   Payload is an encoded UTF-8 JSON dictionary.
*   **Key Functions:**
    *   `send_message(sock, payload)`: Packs length header and payload bytes, transmitting them atomically using `sock.sendall()`.
    *   `receive_message(sock)`: Reads exactly 4 bytes to determine payload length, then loops reading until the full packet is buffered before returning `json.loads(data)`.
*   **Packet Types:**
    *   `DISCOVERY_REQUEST` / `DISCOVERY_RESPONSE`: Neighbor and degree gossip.
    *   `CONNECT_REQUEST` / `CONNECT_ACCEPT` / `DISCONNECT`: Topological rewiring handshakes.
    *   `CONTROL_START_TRANSFER`: C2 command to initiate a file transfer.
    *   `DATA_PACKET`: P2P routed data with TTL, route path, and payload.
    *   `TRANSFER_ACK`: End-to-end receipt reported back to Tracker.

---

### 3. `src/network/tracker.py` — Bootstrap Registry & C2 Telemetry
A lightweight Flask service running on port 5002. **It does NOT route any P2P file data.**

*   **Primary Roles:**
    1.  **Bootstrap DNS:** New nodes query `/api/tracker/register` upon startup to receive initial peer IP addresses.
    2.  **Telemetry Aggregator:** Nodes submit periodic heartbeats (`/api/tracker/heartbeat`) and event telemetry (packets routed, packets dropped).
    3.  **Command & Control (C2) Gateway:** Bridges frontend UI commands to physical containers:
        *   `GET /api/network/state`: Aggregated live node status and active TCP edges.
        *   `POST /api/transfer/start`: Dispatches a TCP transfer trigger to a source container.
        *   `POST /api/node/terminate`: Sends `CONTROL_SHUTDOWN` to test churn resilience.
        *   `POST /api/node/toggle_defector`: Dynamically infects/cures a node as an adversarial defector.

---

## 🛠️ Critical Distributed Systems Bug Fixes

Building physical emulation exposed multiple distributed systems challenges that do not appear in pure math simulations:

1.  **The "66/75 Nodes" Dropping Bug (Heartbeat Desynchronization):**
    *   *Issue:* UI randomly reported 7-9 nodes offline despite Docker containers running.
    *   *Root Cause:* Nodes were blocking on synchronous HTTP telemetry calls (`requests.post`) to the Tracker. If the Tracker delayed responding, the node's thread hung, missing its heartbeat window.
    *   *Resolution:* Injected strict `timeout=2.0` on all node-side HTTP calls with fallback exception handling. Relaxed tracker heartbeat prune window to 30 seconds to accommodate 3–6s random OODA sleep cycles.
2.  **Half-Duplex TCP Socket Deadlock:**
    *   *Issue:* Outbound TCP sockets established during rewiring deadlocked when the peer attempted to respond simultaneously.
    *   *Resolution:* Every outbound connection now immediately spawns a dedicated background client daemon thread before proceeding with application logic.
3.  **Socket Timeout Thread Death:**
    *   *Issue:* Initial connection timeouts on sockets caused background listener threads to terminate unexpectedly.
    *   *Resolution:* Cleared socket timeouts (`sock.settimeout(None)`) immediately following successful handshakes, keeping long-lived TCP connections open.

---

## 🚀 How to Run the Physical Docker Swarm

### Prerequisites
*   Docker Desktop installed and running.
*   Terminal with `docker compose` available.

### 1. Build and Launch the Swarm (75 Nodes)
```bash
# Build base image and start 1 Tracker + 75 peer containers:
docker compose up -d --build --force-recreate
```

### 2. Verify Swarm Status
```bash
# Check container status:
docker compose ps

# View Tracker registration logs:
docker compose logs -f tracker

# View a specific node's OODA loop activity:
docker compose logs -f node_1
```

### 3. Dynamically Scale the Swarm
Scale up or down without taking the network down:
```bash
docker compose up -d --scale node=65 --scale defector=10 --no-recreate
```

### 4. Teardown
```bash
docker compose down -v
```
