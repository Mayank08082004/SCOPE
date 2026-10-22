# SCOPE: Core Simulation Engine (Phase 1 & 2)

Welcome to the **Core Simulation Engine** of SCOPE (Strategic Centrality-driven Overlay P2P Evolution). This subsystem handles the mathematical modeling, algorithmic evolution, and graph-theoretic metrics of the peer-to-peer overlay network.

---

## 📌 Engine Architecture

The core engine models a decentralized network as a **Complex Adaptive System (CAS)** where autonomous agents continuously optimize their local topology without central coordination.

```
                    ┌─────────────────────────┐
                    │      src/config.py      │
                    │   (Simulation Physics)  │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │   src/agent.py    │           │ src/simulation.py │
       │ (PeerAgent & OODA)│◄──────────┤  (World Engine)   │
       └───────────────────┘           └─────────┬─────────┘
                                                 │
                                 ┌───────────────┴───────────────┐
                                 ▼                               ▼
                       ┌───────────────────┐           ┌───────────────────┐
                       │      main.py      │           │      app.py       │
                       │ (Offline CLI/Plot)│           │  (Flask REST API) │
                       └───────────────────┘           └───────────────────┘
```

---

## 📂 Source Code Breakdown

### 1. `src/config.py` — The Simulation Constants ("Laws of Physics")
Centralizes all global simulation hyper-parameters, game-theoretic weights, and algorithmic thresholds:

*   **Simulation Parameters:**
    *   `NUM_NODES = 500`: Default network size for the mathematical model (scales to 50,000+ with Numba JIT).
    *   `INITIAL_DEGREE = 4`: Average number of random connections per node on startup, modeling an unstructured Erdős–Rényi graph.
    *   `ITERATIONS = 50`: Evolutionary loop execution ticks.
    *   `REWIRING_PROB = 0.2`: Churn / activity probability (each step, 20% of agents wake up and evaluate rewiring).
*   **Game Theoretic Utility Weights:**
    *   `ALPHA = 2.0`: Centrality weight. Rewards connecting to high-degree hubs.
    *   `BETA = 0.6`: Maintenance cost penalty. Discourages node over-connection and resource exhaustion.
    *   `GAMMA = 1.0`: Social similarity weight (Triadic Closure). Rewards connections sharing mutual neighbors.
    *   `DELTA_WEIGHT = 0.3`: Proof-of-Throughput weight (Phase 4 addition). Rewards connections to active bandwidth contributors and penalizes free-riders/defectors.
*   **Routing & Incentive Parameters:**
    *   `QUERY_TTL = 20`: Maximum hop count before a Gradient Ascent packet times out (`FAILED_TTL`).
    *   `NUM_SEARCH_QUERIES = 500`: Sample size for evaluating file discovery efficiency.
    *   `L = 100`, `k = 0.5`, `x0 = 10`: Logistic Bandwidth parameters ($L$ = Max Bandwidth in Mbps, $k$ = Steepness, $x0$ = Midpoint degree threshold).

---

### 2. `src/agent.py` — The Peer Agent & The OODA Loop
Houses the `PeerAgent` class, encapsulating the decision loop of each autonomous node:

*   **State & Memory:**
    *   `self.memory`: Capped bounded set (default max: 100 entries) acting as an LRU-like cache of discovered peers via 2-hop gossip.
*   **The OODA Loop:**
    1.  **Observe (`agent.observe`):** Gathers local topology data from immediate neighbors and their neighbors (2-hop peer discovery).
    2.  **Orient (`agent.calculate_utility`):** Evaluates connection utility using JIT-compiled mathematical functions.
    3.  **Decide (`agent.decide` / `agent.act`):** Identifies the lowest-utility current edge and compares it against highest-utility known candidates in `memory`.
    4.  **Act (`agent.act`):** Executes edge rewiring if candidate utility exceeds the threshold with **Hysteresis** ($1.1\times$).
*   **Key Algorithms:**
    *   **Utility Maximization (Proof-of-Throughput Nash Equilibrium):**
        $$U_j = \alpha \cdot \ln(1 + k_j) - \beta \cdot \left(\frac{k_i}{10}\right) + \gamma \cdot S_{ij} + \delta \cdot T_j$$
        Where $k_j$ is the candidate's degree, $k_i$ is current agent's degree, $S_{ij} = \frac{|N(i) \cap N(j)|}{|N(i) \cup N(j)|}$ (Jaccard similarity), and $T_j$ is the candidate's normalized bandwidth throughput ($T_j \in [0, 1]$).
    *   **Hysteresis Threshold:** Prevents high-frequency topological oscillation:
        $$U_{\text{candidate}} > 1.1 \cdot U_{\text{worst\_current}}$$
    *   **Differential Service Incentive:** Throttles free-riders using a Logistic Bandwidth curve:
        $$\text{Bandwidth}(k_i) = \frac{L}{1 + e^{-k(k_i - x_0)}}$$
    *   **Gradient Ascent Routing:** Forwards search queries greedily to the highest-degree unvisited neighbor in the hop path.

---

### 3. `src/simulation.py` — The World Engine
Orchestrates the environment, execution cycles, and statistical metric aggregation:

*   `initialize_graph()`: Constructs an Erdős–Rényi random graph $G(N, p)$ and enforces connectivity (`nx.is_connected`).
*   `run_simulation()`: Executes synchronous iterations:
    1.  Randomly samples active agents according to `REWIRING_PROB`.
    2.  Invokes `observe()` and `act()` on each active peer.
    3.  Records structural telemetry per step: **Average Path Length (APL)** and **Average Clustering Coefficient**.
*   `test_routing_performance()`: Benchmarks Gradient Ascent search performance across 500 random pairs against the un-evolved baseline.
*   **Why Synchronous Over Multiprocessing?**
    Early implementations used `ProcessPoolExecutor`. On macOS (`spawn` process creation), pickling large NetworkX graphs across process boundaries incurred massive IPC overhead and caused `BrokenProcessPool` failures. Synchronous loops combined with Numba JIT proved significantly faster and completely stable.

---

### 4. Integration Entry Points

*   **`main.py` (CLI Evaluation):**
    Runs the simulation offline, prints baseline vs evolved comparison metrics to stdout, and generates a 4-panel publication-ready visualization (`scope_results.png`):
    *   APL decay over iterations.
    *   Clustering coefficient growth.
    *   Degree-sorted Adjacency Matrix heatmap (revealing the dense Core Hubs).
    *   Logistic Incentive S-Curve (Degree vs Download Speed).
*   **`app.py` (Flask REST API Backend):**
    Serves Phase 2 telemetry to the React dashboard (`SimulationDashboard.jsx`):
    *   `POST /api/init`: Initializes a new graph with custom $\alpha, \beta, \gamma$.
    *   `POST /api/evolve`: Steps the simulation forward by $N$ iterations.
    *   `GET /api/metrics`: Returns time-series APL, clustering, and degree distributions.
    *   `GET /api/graph`: Returns the current node/edge adjacency payload for D3 visualization.

---

## 🚀 How to Run the Simulation

### Option A: Offline CLI Simulation (Generates Charts)
```bash
# From workspace root:
pip install -r requirements.txt
python main.py
```
*Output: Generates `scope_results.png` and logs routing efficiency to terminal.*

### Option B: Flask API Server (Connects to Web UI)
```bash
# From workspace root:
python app.py
```
*Server runs on `http://localhost:5001`. Connects with the React dashboard on `http://localhost:5173`.*

### Option C: Ablation Study Runner (Phase 4 Journal Benchmarks)
```bash
# Quick smoke test (N=500, 3 seeds, ~2 min):
python3 -m tests.ablation_runner --quick

# Full publication-quality run (N=5000, 10 seeds):
python3 -m tests.ablation_runner
```
*Outputs: Generates `results/ablation_results.csv`, `results/ablation_summary.csv`, and 4 publication figures (PDF + PNG) in `results/figures/`.*

---

## 📊 Phase 2 Benchmark Results

Tested on a 500-node network over 50 iterations:

| Metric | Random Baseline | SCOPE Evolved Network | Improvement |
| :--- | :--- | :--- | :--- |
| **Average Path Length (APL)** | 5.08 hops | **2.65 hops** | **-47.8% latency reduction** |
| **Clustering Coefficient** | 0.0079 | **0.3931** | **+4,875% social clustering** |
| **Search Routing Hops** | 10.13 hops | **2.91 hops** | **-71.3% hop reduction** |
| **Search Success Rate (TTL=20)** | 26.2% | **73.4%** | **~2.8× higher reliability** |
| **Bandwidth (Core Hubs vs Leaves)**| 1.67 Mbps | **46.45 Mbps** | **27.9× incentive multiplier** |
