# SCOPE: Strategic Centrality-driven Overlay P2P Evolution

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Project Overview
**SCOPE** (Strategic Centrality-driven Overlay P2P Evolution) is an advanced network simulation framework designed to model the self-organization of decentralized Peer-to-Peer (P2P) networks. 

Unlike traditional static topologies, SCOPE models the network as a **Complex Adaptive System (CAS)**. Autonomous "Peer Agents" continuously optimize their local connections based on a strategic utility function, intentionally evolving the network from a random state into an optimized **Nested Core-Periphery Topology**. This structure significantly reduces routing latency, minimizes redundant traffic, and enhances robustness against node failures.

## 🚀 Key Features
* **Evolutionary Topology:** Agents autonomously rewire connections to form a "Super-Peer" core without central coordination.
* **Smart Routing Engine:** Implements **Probabilistic Gradient Ascent** routing with agent memory (2-hop lookahead) to simulate realistic file search.
* **Strategic Utility Function:** Agents make decisions based on Centrality (Benefit), Connection Cost (Penalty), and Social Similarity.
* **Real-time Visualization:** Generates live metrics for Path Length, Clustering Coefficient, and Adjacency Heatmaps.

---

## 📂 Project Structure
The project is modularized for scalability and ease of maintenance:

```text
SCOPE/
│
├── main.py                 # Entry point: Runs evolution, testing, and plotting
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
└── src/                    # Core Logic Modules
    ├── __init__.py
    ├── config.py           # Configuration parameters (Physics of the simulation)
    ├── agent.py            # PeerAgent class (The "Brain": Utility logic & Memory)
    └── simulation.py       # Simulation Engine (Evolution Loop & Search Tests)
```
## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/SCOPE.git](https://github.com/your-username/SCOPE.git)
cd SCOPE
```
### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Run the Simulation
```bash
python main.py
```

### What Happens When You Run It?
1.  **Initialization:** A random Erdős–Rényi graph (500 nodes) is created.
2.  **Evolution Phase:** The simulation runs for `N` iterations. Agents wake up, observe neighbors, and rewire links to maximize utility.
3.  **Search Test Phase:** The system runs 500 file search queries using the evolved topology to measure operational efficiency.
4.  **Visualization:** A dashboard of 3 graphs is generated showing the network's improvement over time.

---

## ⚙️ Configuration

You can tune the "physics" of the simulation in `src/config.py`.

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `NUM_NODES` | 500 | Total number of agents in the network. |
| `ITERATIONS` | 50 | Duration of the evolutionary phase. |
| `REWIRING_PROB` | 0.2 | Probability of an agent acting in a single step. |
| `ALPHA` | 2.0 | **Benefit Weight:** Importance of connecting to high-degree Hubs. |
| `BETA` | 0.6 | **Cost Weight:** Penalty for maintaining too many connections. |
| `GAMMA` | 1.0 | **Social Weight:** Bonus for clustering (connecting to friends-of-friends). |
| `QUERY_TTL` | 20 | **Time-To-Live:** Max hops a search query can travel before failing. |

---

## 🧠 How It Works

### 1. The Utility Function (The "Brain")
Every agent decides who to connect with based on this formula:

$$U_j = \alpha \cdot \ln(1 + k_j) - \beta \cdot C_i + \gamma \cdot S_{ij}$$

* **$\alpha$ (Centrality):** Agents prefer popular nodes (Hubs).
* **$\beta$ (Cost):** Agents avoid having too many links (maintenance cost).
* **$\gamma$ (Similarity):** Agents prefer nodes that share common neighbors (Clustering).

### 2. The Search Algorithm (The "Operation")
Once the topology is built, we test it using a **Hybrid Search Protocol**:
* **Memory Check:** The agent checks its local memory (up to 100 peers) to see if it knows the target location.
* **Probabilistic Gradient Ascent:** If the target is unknown, the query is forwarded to a neighbor. The choice is weighted by degree centrality (higher probability of asking a popular node), allowing the search to escape local traps.

---

## 📊 Results & Visualization

The simulation outputs three key performance indicators:

### 1. Optimization of Routing Efficiency
* **Metric:** Average Path Length (Hops).
* **Goal:** Decrease (closer to 2-3 hops).
* **Result:** Shows how quickly the network shrinks (Small World effect).

### 2. Emergence of Social Clustering
* **Metric:** Clustering Coefficient.
* **Goal:** Increase.
* **Result:** Proven robustness against random node failures.

### 3. Adjacency Matrix Heatmap
* **Visual:** A dense block in the top-left corner.
* **Meaning:** Visual proof of a **Nested Core-Periphery** structure (Hubs connecting to Hubs).

---

## 📦 Dependencies

* `networkx` - Graph creation and metric calculation.
* `matplotlib` & `seaborn` - Plotting and visualization.
* `numpy` - Numerical operations.
* `tqdm` - Progress bars.

---

## 📄 License

This project is licensed under the MIT License.