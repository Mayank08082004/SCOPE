# SCOPE: Strategic Centrality-driven Overlay P2P Evolution

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![React](https://img.shields.io/badge/React-Vite-blue)
![Docker](https://img.shields.io/badge/Docker-Swarm-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Phase_3-Complete-success)

## 📌 Project Overview
**SCOPE** (Strategic Centrality-driven Overlay P2P Evolution) is an advanced network simulation framework designed to model the self-organization of decentralized Peer-to-Peer (P2P) networks. 

Unlike traditional static topologies, SCOPE models the network as a **Complex Adaptive System (CAS)**. Autonomous "Peer Agents" continuously optimize their local connections based on a strategic utility function, intentionally evolving the network from a random state into an optimized **Nested Core-Periphery Topology**. 

SCOPE is built in three phases:
*   **Phase 1 & 2:** A mathematical array-based simulation using Multiprocessing and LLVM JIT optimization (Numba) to evolve 50,000+ nodes instantly.
*   **Phase 3:** A **Physical Docker Swarm Simulation** featuring up to 75+ isolated containers running real TCP socket communications, managed by a live React Command & Control (C2) Dashboard.

---

## 📂 Complete Repository Breakdown

### 1. The Core Simulation Engine (Phase 1 & 2)
Located in `src/` and the root directory. This engine handles the mathematical graph evolution.

*   **`src/config.py`**: The "Laws of Physics." Contains all constants: `NUM_NODES`, `REWIRING_PROB`, the Game Theory utility weights (`ALPHA`, `BETA`, `GAMMA`), and routing parameters.
*   **`src/agent.py`**: Contains the `PeerAgent` class. Implements the **OODA Loop** (Observe, Orient, Decide, Act). It uses Numba `@jit` to rapidly calculate the topological utility of neighboring nodes.
*   **`src/simulation.py`**: The World Engine. Uses `networkx` to initialize random Erdős–Rényi graphs. Originally explored `ProcessPoolExecutor` for parallelization, but transitioned to a highly-optimized synchronous execution model to eliminate massive IPC pickling overhead and bypass macOS multiprocessing (`spawn` vs `fork`) compatibility bottlenecks. Calculates Graph Average Path Length (APL) and Clustering Coefficients.
*   **`main.py`**: The CLI entry point for running the mathematical simulation entirely offline in the terminal. Uses `matplotlib` to generate statistical charts (`scope_results.png`).
*   **`app.py`**: The Flask API backend for Phase 2. Exposes endpoints to control the mathematical array simulation and serve Graph metrics to the web dashboard.

### 2. The Physical Emulation Engine (Phase 3)
Located in `src/network/`. This engine transitions the math into real-world networking via isolated docker containers.

*   **`src/network/node.py`**: The physical manifestation of a Peer. Runs continuously inside an isolated Docker container. Maintains a multithreaded architecture (Main thread, Server TCP accept thread, OODA Loop background thread, and spawned client daemon threads for Full-Duplex asynchronous read/writes).
*   **`src/network/protocol.py`**: Implements a custom binary-prefixed JSON protocol for TCP socket communication. Contains `send_message` and `receive_message` with safe byte-handling logic.
*   **`src/network/tracker.py`**: A central Flask API acting as a "DNS Server". Nodes register their physical IPs here upon boot. It maintains network state using a precise 30-second heartbeat threshold, carefully tuned to accommodate the asynchronous sleep cycles of the nodes' OODA loops without causing desynchronization. It acts as the C2 (Command & Control) server for the dashboard to orchestrate live file transfers, toggle defectors, and gather telemetry. **It does NOT route traffic.**
*   **`docker-compose.yml`**: The orchestration file that spins up 1 tracker and 75 physical instances of `node.py` (including malicious Defector variants) on a custom bridged subnet.
*   **`Dockerfile`**: The container blueprint for running `node.py` and `tracker.py`.

### 3. The React C2 Dashboard (Frontend)
Located in `frontend/`. Built with Vite, React, TailwindCSS, and ShadCN components.

*   **`frontend/src/App.jsx`**: The main React Router setting up navigation between the Simulation (Phase 2) and Network (Phase 3) dashboards.
*   **`frontend/src/pages/SimulationDashboard.jsx`**: The Phase 2 UI. Connects to `app.py`. Provides sliders to tweak Alpha, Beta, and Gamma in real-time and visualize the mathematical evolution of the array-based graph.
*   **`frontend/src/pages/NetworkDashboard.jsx`**: The Phase 3 UI. Connects to `tracker.py` (Port 5002). Visualizes the physical Docker Swarm in real-time. Allows users to click on specific containers to execute P2P File Transfers, terminate instances, or infect them as Defectors.
*   **`frontend/src/components/dashboard/NetworkGraph.jsx`**: A shared visualization component utilizing `d3-force` (via `react-force-graph-2d`) to render the physical TCP connections as a dynamic gravity-based web.
*   **`frontend/src/hooks/useSimulation.js`**: A custom React hook managing the API polling states to keep the dashboards completely synchronized with the backend.

### 4. Documentation & Research Files
*   **`project_walkthrough.md`**: An exhaustive educational guide detailing the theoretical concepts of CAS, a step-by-step trace of a single OODA loop iteration, and the real-world networking mechanics of Phase 3.
*   **`presentation.md`**: A high-level executive summary of the Phase 3 architecture, the bugs patched, and the discoveries made (e.g., The Dead-End Phenomenon).
*   **`research_paper_outline.md`**: The academic blueprint for writing a scholarly paper based on this simulation's findings.
*   **`adversarial_analysis.md`**: Deep dive into the Game Theory vulnerabilities of the utility function when subjected to Sybil attacks.
*   **`user-frontend-commands.md` & `assessment_report.md`**: Development logs and UI component lists.

---

## ⚙️ How Everything Interacts

### The Phase 2 Flow (Mathematical Simulation)
1.  The user opens `SimulationDashboard.jsx` (Frontend).
2.  The UI sends a POST request with Alpha/Beta/Gamma weights to `app.py` (Backend).
3.  `app.py` imports `src/simulation.py`.
4.  `simulation.py` creates 500 virtual nodes using `src/agent.py`.
5.  The agents execute mathematical OODA loops using Numba arrays.
6.  `simulation.py` returns the final Graph adjacency matrix to `app.py`, which serves it to `SimulationDashboard.jsx` for D3 visualization.

### The Phase 3 Flow (Physical Docker Emulation)
1.  The user runs `docker compose up -d`. This boots 75 containers running `node.py` and 1 container running `tracker.py`.
2.  Each `node.py` establishes its own TCP Server Socket and POSTs its IP address to `tracker.py` (`/api/tracker/register`).
3.  Nodes independently execute OODA loops, reaching out to other containers and opening **real TCP Sockets** (`protocol.py`) to negotiate their topology.
4.  The user opens `NetworkDashboard.jsx` (Frontend). The UI constantly polls `tracker.py` (`/api/network/state`) to render the physical topology.
5.  **P2P Transfer Action:** The user clicks "Execute Transfer" in the UI. The UI POSTs to `tracker.py`, which relays a `CONTROL_START_TRANSFER` command directly to the source `node.py` over TCP.
6.  The source `node.py` routes the packet through its local TCP sockets using Memory-Assisted Gradient Ascent until it reaches the target `node.py`. The result is reported back to the tracker and visualized on the frontend.

---

## 🧠 Core Concepts & Discoveries

### 1. The Utility Function
Agents maximize local utility $U$ using Game Theory:
$$U_j = \alpha \cdot \ln(1 + k_j) - \beta \cdot C_i + \gamma \cdot S_{ij}$$
*   **$\alpha$ (Benefit):** Desire for high-degree Hubs (Centrality).
*   **$\beta$ (Cost):** Penalty for maintenance complexity.
*   **$\gamma$ (Similarity):** Preference for friends-of-friends (Social Clustering).

### 2. Gradient Ascent & The "Dead-End Phenomenon"
During physical file transfers, packets are routed using **Gradient Ascent**—a node passes the packet to its highest-degree neighbor. 
Through live simulation, we proved a limitation of this greedy routing: If a packet gets routed into a dense cluster of Super-Hubs, it bounces around until all local Hubs are visited. If the true target is in a different cluster, the packet runs out of unvisited neighbors and hits a **FAILED_DEADEND**. This proves the absolute necessity of the `self.memory` shortcut logic we built, which acts as a bypass for local maximum traps.

### 3. The "Black Hole" Adversarial Attack
To test resilience, we injected malicious **Defector Nodes**. Defectors spoof their utility values, advertising massive fake degrees to the network. Because the Utility function mathematically rewards high-degree targets, honest nodes flock to these defectors, creating massive topological hubs. When a file transfer routes into a defector, the defector silently drops it, acting as a network black hole.

### 4. Differential Service (Incentive Mechanism)
To prevent "Free-Riders" (nodes that use the network without contributing connections), we implemented a Logistic Bandwidth Throttling function. Hubs with high degrees (contributing heavily) receive up to 100 Mbps, while Leaf nodes (free-riders) are throttled down to ~1.7 Mbps.

---

## 🛠️ Quick Start

### 1. Run the Physical Emulation (Phase 3)
Ensure Docker Desktop is running.
```bash
# Build and deploy the 75-node swarm
docker compose up -d --build --force-recreate

# To scale the swarm dynamically without dropping the network:
docker compose up -d --scale node=65 --scale defector=10 --no-recreate
```

### 2. Run the React Web Dashboard
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Access the interactive dashboard at `http://localhost:5173`.*

### 3. Run the Legacy Offline Simulation (Phase 2)
To run the purely mathematical array simulation:
```bash
pip install -r requirements.txt
python app.py
```
*The Phase 2 Flask API runs on `http://localhost:5001`.*