# SCOPE: Strategic Centrality-driven Overlay P2P Evolution

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![React](https://img.shields.io/badge/React-Vite-blue)
![Docker](https://img.shields.io/badge/Docker-Swarm-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Phase_3-Complete-success)

## 📌 Project Overview
**SCOPE** (Strategic Centrality-driven Overlay P2P Evolution) is an advanced network simulation framework designed to model the self-organization of decentralized Peer-to-Peer (P2P) networks. 

Unlike traditional static topologies, SCOPE models the network as a **Complex Adaptive System (CAS)**. Autonomous "Peer Agents" continuously optimize their local connections based on a strategic utility function, intentionally evolving the network from a random state into an optimized **Nested Core-Periphery Topology**. 

Phase 3 introduces a full **Physical Docker Swarm Simulation** (up to 75+ isolated containers running real TCP socket communications), a live React C2 Dashboard, Adversarial Defector nodes ("Black Holes"), and real-time routing simulations using memory-assisted Gradient Ascent.

## 🚀 Key Features
* **Evolutionary Topology:** Agents autonomously rewire connections to form a "Super-Peer" core without central coordination.
* **Physical Network Emulation (Phase 3):** Uses Docker Compose to spin up dozens of isolated `node.py` containers that talk to each other over real local TCP sockets, tracked by a central `tracker.py`.
* **React C2 Web Dashboard:** A live, interactive dashboard built with Vite and TailwindCSS to monitor the physical network topology, inject file transfers, terminate nodes, and toggle defectors in real-time.
* **Incentive Mechanism (Differential Service):** A logistic bandwidth throttling function that rewards high-centrality Hubs with up to **75x faster service** than leaf nodes.
* **Adversarial Modeling:** Introduces malicious "Defectors" to test the network's resilience against Sybil/Black-Hole routing attacks by inflating their advertised degree to lure and drop packets.

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