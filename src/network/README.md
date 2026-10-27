# SCOPE: Physical Emulation Engine (Phase 3 & Phase 4 Swarm)

Welcome to the **Physical Emulation Engine** of SCOPE. This subsystem transitions the theoretical and mathematical graph models from Phase 1 & 2 into real-world distributed systems engineering running on **isolated Docker containers** communicating via **raw TCP sockets**.

**Phase 4 (Advanced Systems & Routing)** adds backtracking routing, distributed betweenness telemetry, Proof-of-Throughput defector defense, ACK-based quarantine, and C2 transport hardening.

---

## 📌 Subsystem Architecture

The physical engine deploys up to 75+ containerized peer nodes communicating directly with one another over an isolated Docker bridge network (`scope_net`). A central lightweight Command & Control (C2) Tracker manages bootstrap registration, telemetry, and **betweenness centrality computation** for the live React dashboard.

```
                               ┌─────────────────────────────┐
                               │   React C2 Dashboard (UI)   │
                               │   (http://localhost:5173)   │
                               └──────────────┬──────────────┘
                                              │ HTTP Polling / C2 Commands
                                              │ (X-C2-Auth-Token header)
                                              ▼
                               ┌─────────────────────────────┐
                               │     src/network/tracker.py  │
                               │  (Bootstrap DNS & C2 Server) │
                               │  + Betweenness Computation  │
                               │        (Port: 5002)         │
                               └──────────────┬──────────────┘
                                              │ Registration, Heartbeats,
                                              │ Betweenness Scores
             ┌────────────────────────────────┴────────────────────────────────┐
             │                                                                 │
             ▼                                                                 ▼
 ┌───────────────────────┐                                         ┌───────────────────────┐
 │  src/network/node.py  │       Raw Localhost TCP Sockets         │  src/network/node.py  │
 │ (Container: node_1)   │◄───────────────────────────────────────►│ (Container: node_2)   │
 │ - Port: 5000          │        (Custom Binary JSON Framing)     │ - Port: 5000          │
 │ - Honest Peer         │     + BACKTRACK / TRANSFER_ACK msgs     │ - Defector (Sybil)    │
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
    *   **ACK Monitor Thread** *(Phase 4)*: Periodically checks for timed-out transfer ACKs and flags unresponsive peers as suspicious.
    *   **Spawned Client Daemon Threads:** For every inbound or outbound TCP connection, a dedicated daemon thread is spawned to handle streaming socket reads. This ensures **Full-Duplex asynchronous I/O** without socket deadlocks.

*   **Routing Logic — Phase 4 Backtracking State Machine:**
    *   When routing a `FILE_TRANSFER`, the node checks if the target IP is in its immediate neighbor table (memory-assisted shortcut).
    *   If not, it forwards to the highest-degree unvisited neighbor via gradient-ascent.
    *   **Phase 4 Backtracking:** When a packet hits a dead-end (all neighbors visited), instead of failing with `FAILED_DEADEND`, the node sends a `BACKTRACK` message to the previous hop with an `attempted` set. The previous hop then tries the *next-best* degree neighbor, excluding already-attempted nodes.
    *   Multi-level backtracking is supported: if the second hop also dead-ends, it backtracks again.
    *   Target: **>95% delivery success** by eliminating the dead-end failure mode.

*   **Phase 4 — Proof-of-Throughput (δ Term):**
    *   Imports `DELTA_WEIGHT` from `src.config`.
    *   Tracks per-peer delivery statistics (`peer_delivery_stats`): sent count and acknowledged count.
    *   Computes `peer_throughput = acked / sent` (T_ij ∈ [0.0, 1.0]).
    *   Suspicious/defector peers get T_ij = 0.001.
    *   All `_jit_calculate_utility` calls now pass the full 10-argument signature including `DELTA_WEIGHT` and `peer_throughput`.

*   **Phase 4 — Defector Quarantine via ACK Tracking:**
    *   Destination nodes send `TRANSFER_ACK` messages back to the forwarding node upon successful receipt.
    *   `pending_acks` dict tracks outstanding ACKs with timestamps.
    *   Background `_monitor_pending_acks` thread flags peers with ≥3 unacknowledged transfers (within 10s timeout) as suspicious.
    *   Suspicious peers are automatically penalized in utility calculations (T_ij = 0.001), causing them to be disconnected at the next OODA cycle.
    *   Rehabilitation: if a suspicious peer later acknowledges transfers (>50% success rate), it is removed from the suspicious set.

*   **Phase 4 — C2 Transport Hardening:**
    *   All C2 commands (`CONTROL_SHUTDOWN`, `CONTROL_TOGGLE_DEFECTOR`, `CONTROL_CURE_DEFECTOR`) require an `auth_token` field in the message payload.
    *   The token is read from the `C2_AUTH_TOKEN` environment variable (default: `SCOPE_DEFAULT_C2_SECRET`).
    *   Commands with invalid or missing tokens are rejected with a log warning.

*   **Defector Mode (Adversarial Sybil Node):**
    *   Defectors report an artificially inflated degree (`actual_degree * 3 + 5`) in response to TCP degree queries.
    *   Honest nodes eagerly wire to defectors due to the α utility benefit.
    *   Upon receiving a `DATA_PACKET`, the defector silently drops it, acting as a **Black Hole** and reporting dropped telemetry to the Tracker.

---

### 2. `src/network/protocol.py` — Custom Binary-Prefixed TCP Framing
Raw TCP sockets provide a continuous byte stream without built-in message boundaries. `protocol.py` provides deterministic packet framing:

*   **Framing Mechanism:**
    *   Every message begins with a **4-byte big-endian unsigned integer** (`!I`) representing the byte-length of the following JSON payload.
    *   Payload is an encoded UTF-8 JSON dictionary.
*   **Key Functions:**
    *   `send_message(sock, payload)`: Packs length header and payload bytes, transmitting them atomically using `sock.sendall()`.
    *   `receive_message(sock)`: Reads exactly 4 bytes to determine payload length, then loops reading until the full packet is buffered before returning `json.loads(data)`.
*   **Packet Types (Phase 4 additions marked with 🆕):**
    *   `HANDSHAKE`: Initial connection establishment with peer ID, IP, port.
    *   `GET_DEGREE` / `DEGREE_RES`: Neighbor degree gossip.
    *   `GET_NEIGHBORS` / `NEIGHBORS_RES`: Neighbor list gossip.
    *   `DATA_PACKET`: P2P routed data with TTL.
    *   `FILE_TRANSFER`: File transfer routing with path, TTL, 🆕 `attempted` set, 🆕 `backtracks` array.
    *   🆕 `BACKTRACK`: Dead-end node requests previous hop to try next-best neighbor.
    *   🆕 `TRANSFER_ACK`: Destination confirms successful receipt of a transfer.
    *   `CONTROL_START_TRANSFER`: C2 command to initiate a file transfer.
    *   `CONTROL_SHUTDOWN`: C2 kill command (🆕 requires `auth_token`).
    *   `CONTROL_TOGGLE_DEFECTOR`: C2 defector toggle (🆕 requires `auth_token`).
    *   🆕 `CONTROL_CURE_DEFECTOR`: C2 command to rehabilitate a defector node.

---

### 3. `src/network/tracker.py` — Bootstrap Registry, C2 Telemetry & Betweenness Engine
A lightweight Flask service running on port 5002. **It does NOT route any P2P file data.**

*   **Primary Roles:**
    1.  **Bootstrap DNS:** New nodes query `/api/tracker/register` upon startup to receive initial peer IP addresses.
    2.  **Telemetry Aggregator:** Nodes submit periodic heartbeats (`/api/tracker/heartbeat`) and event telemetry (packets routed, packets dropped).
    3.  🆕 **Betweenness Centrality Engine:** Background thread recomputes sampled betweenness centrality every 15 seconds from the active edge topology. Scores are normalized to [0.0, 1.0] and streamed to nodes via heartbeat responses.
    4.  **Command & Control (C2) Gateway:** Bridges frontend UI commands to physical containers (🆕 with auth token validation):
        *   `GET /api/network/state`: Aggregated live node status, active TCP edges, 🆕 and betweenness scores.
        *   `POST /api/tracker/transfer`: Dispatches a TCP transfer trigger to a source container.
        *   `POST /api/tracker/control`: Sends C2 commands (KILL, TOGGLE_DEFECTOR, 🆕 CURE_DEFECTOR) — 🆕 requires `X-C2-Auth-Token` header.
        *   🆕 `GET /api/tracker/betweenness`: Debug endpoint returning all current betweenness scores.

*   **Phase 4 — Transfer Result Schema:**
    Transfer results now include the `backtracks` array for frontend animation:
    ```json
    {
        "status": "SUCCESS",
        "path": ["node_1", "node_14", "node_42", "node_60"],
        "backtracks": [["node_14", "node_22"]]
    }
    ```

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

### 5. Phase 4 — C2 Authentication
The `C2_AUTH_TOKEN` environment variable is set in `docker-compose.yml`. To change the token:
```yaml
environment:
  - C2_AUTH_TOKEN=your_custom_secret_here
```
The token must match across the tracker and all nodes. Frontend requests to `/api/tracker/control` must include the `X-C2-Auth-Token` header.
