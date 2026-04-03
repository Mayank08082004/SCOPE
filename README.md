# SCOPE: Strategic Centrality-driven Overlay P2P Evolution

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Phase_2-Complete-success)

## 📌 Project Overview
**SCOPE** (Strategic Centrality-driven Overlay P2P Evolution) is an advanced network simulation framework designed to model the self-organization of decentralized Peer-to-Peer (P2P) networks. 

Unlike traditional static topologies, SCOPE models the network as a **Complex Adaptive System (CAS)**. Autonomous "Peer Agents" continuously optimize their local connections based on a strategic utility function, intentionally evolving the network from a random state into an optimized **Nested Core-Periphery Topology**. Phase 2 adds operational intelligence through **Gradient Ascent routing** and a **Logistic Incentive Mechanism** to solve the free-rider problem.

## 🚀 Key Features (Phase 1 & 2)
* **Evolutionary Topology:** Agents autonomously rewire connections to form a "Super-Peer" core without central coordination.
* **Operational Search Engine:** Implements **Gradient Ascent** routing that achieves **~2.4 hops** compared to ~10+ in random networks.
* **Incentive Mechanism (Differential Service):** A logistic bandwidth throttling function that rewards high-centrality Hubs with up to **75x faster service** than leaf nodes.
* **Strategic Utility Function:** Decisions driven by Centrality Benefit, Connection Cost, and Social Similarity (Clustering).
* **2x2 Analytics Dashboard:** Live metrics for APL, Clustering, Adjacency Matrices, and Bandwidth Distribution.

---

## 📂 Project Structure
```text
SCOPE/
│
├── main.py                 # Dashboard & Report entry point
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
└── src/                    
    ├── config.py           # Simulation constants & weights
    ├── agent.py            # PeerAgent (Utility, Routing, & Bandwidth Throttling)
    └── simulation.py       # Evolution Loop & Operational Benchmarking
```

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
### 2. Run Phase 2 Simulation
```bash
python main.py
```

### What Happens?
1. **Baseline Test:** Runs 500 search queries on an initial **Random Graph**.
2. **Evolution Phase:** Agents perform 50 iterations of OODA (Observe-Orient-Decide-Act) cycles.
3. **Strategic Test:** Runs 500 search queries on the **Optimized Network**.
4. **Incentive Analysis:** Calculates download speeds for every node based on its centrality rank.
5. **Visualization:** Generates a 4-plot dashboard showing topological and operational success.

---

## 🧠 Core Logic

### 1. The Utility Function (The "Brain")
Agents maximize local utility $U$:
$$U_j = \alpha \cdot \ln(1 + k_j) - \beta \cdot C_i + \gamma \cdot S_{ij}$$
* **$\alpha$ (Benefit):** Desire for high-degree Hubs.
* **$\beta$ (Cost):** Penalty for maintenance complexity.
* **$\gamma$ (Similarity):** Preference for friends-of-friends (Social Clustering).

### 2. Incentive Mechanism (Differential Service)
To prevent "Free-Riders," bandwidth $B$ is a **logistic function** of centrality (degree $d$):
$$B(d) = \frac{L}{1 + e^{-k(d - d_0)}}$$
* **Result:** "Hubs" receive capped premium service (100Mbps), while "Leaves" are limited to baseline speeds (~1Mbps).

---

## 📊 Phase 2 Operational Results

| Metric | Random (Baseline) | Strategic (SCOPE) | Improvement |
| :--- | :--- | :--- | :--- |
| **Avg. Search Hops** | ~10.85 | **~2.44** | **77% Reduction** |
| **Search Success Rate** | ~23% | **~54%** | **2.3x Increase** |
| **Service Speed** | Uniform | Differential | Hubs: 73x Faster |

---

## 📈 Visualization Dashboard
The system generates four critical plots:
1. **Optimization of Routing:** Shows APL shrinking towards the 2-hop target.
2. **Social Clustering:** Marks the emergence of local communities.
3. **Adjacency Matrix:** Visual proof of the dense **Nested Core**.
4. **Incentive Curve:** Scatter plot of Degree vs. Bandwidth showing the logistic reward system.

---

## 📄 License
This project is licensed under the MIT License.