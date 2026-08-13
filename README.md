# SCOPE: Strategic Centrality-driven Overlay P2P Evolution

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![React](https://img.shields.io/badge/React-Vite-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Phase_2.5-Complete-success)

## 📌 Project Overview
**SCOPE** (Strategic Centrality-driven Overlay P2P Evolution) is an advanced network simulation framework designed to model the self-organization of decentralized Peer-to-Peer (P2P) networks. 

Unlike traditional static topologies, SCOPE models the network as a **Complex Adaptive System (CAS)**. Autonomous "Peer Agents" continuously optimize their local connections based on a strategic utility function, intentionally evolving the network from a random state into an optimized **Nested Core-Periphery Topology**. 

Phase 2 and 2.5 introduce a full interactive Web Dashboard, massive scale (50,000+ nodes) through multiprocessing and LLVM JIT optimization, and adversarial environment testing.

## 🚀 Key Features
* **Evolutionary Topology:** Agents autonomously rewire connections to form a "Super-Peer" core without central coordination.
* **Extreme Scalability (Phase 2.5):** Uses `ProcessPoolExecutor` for parallelizing agent decisions across all CPU cores, and `Numba` `@jit` compilation to run mathematical OODA loops at C/Rust speeds.
* **React Web Dashboard:** A live, interactive dashboard built with Vite and TailwindCSS to monitor network topology, APL, Clustering, and individual node metrics in real-time.
* **Incentive Mechanism (Differential Service):** A logistic bandwidth throttling function that rewards high-centrality Hubs with up to **75x faster service** than leaf nodes.
* **Adversarial Modeling:** Introduces malicious "Defectors" to test the network's resilience against Sybil/Black-Hole routing attacks.

---

## 📂 Project Structure
```text
SCOPE/
│
├── app.py                  # Flask API Backend
├── main.py                 # Offline CLI Benchmark entry point
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── frontend/               # React + Vite Web Dashboard
│   ├── src/components/     # UI Components (Control Panel, Graphs, Inspector)
│   └── README.md
│
└── src/                    
    ├── config.py           # Simulation constants & weights
    ├── agent.py            # PeerAgent (Utility & OODA Loop with Numba JIT)
    └── simulation.py       # Core Multi-core Evolution Loop & Graph Metrics
```

## 🛠️ Quick Start

### 1. Backend Setup
```bash
pip install -r requirements.txt
python app.py
```
*The Flask API will run on `http://localhost:5001`.*

### 2. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Access the interactive dashboard at `http://localhost:5173`.*

---

## 🧠 Core Logic & Adversarial Vulnerabilities

### The Utility Function (The "Brain")
Agents maximize local utility $U$:
$$U_j = \alpha \cdot \ln(1 + k_j) - \beta \cdot C_i + \gamma \cdot S_{ij}$$
* **$\alpha$ (Benefit):** Desire for high-degree Hubs (Centrality).
* **$\beta$ (Cost):** Penalty for maintenance complexity.
* **$\gamma$ (Similarity):** Preference for friends-of-friends (Social Clustering).

### The "Black Hole" Defector Attack
Because the utility equation purely evaluates **Topological Data** (advertised degree) rather than **Physical Throughput**, introducing 10% malicious nodes ("Defectors") reveals a critical vulnerability. Defectors advertise massive degree sizes but provide 0 Mbps bandwidth. Honest nodes, seeking shortest paths, eagerly wire up to these defectors, causing massive topological hubs to form around malicious actors that act as black holes for data packets.

## 📄 License
This project is licensed under the MIT License.