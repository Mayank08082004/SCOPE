# SCOPE: Command & Control (C2) Web Dashboard

The **SCOPE Web Dashboard** is a real-time, interactive Command & Control (C2) interface built for visualizing and orchestrating both the **Phase 2 Mathematical Simulation** and the **Phase 3 Physical Docker Swarm**.

---

## 🚀 Technology Stack

*   **Core Framework:** React 19 + Vite (Fast HMR development tooling)
*   **Routing:** React Router v7 (`react-router-dom`)
*   **Styling:** TailwindCSS v4 with Glassmorphism aesthetic
*   **Component Library:** Radix UI primitives (`@radix-ui/*`) & Lucide React icons
*   **Topology Graph Visualization:** `react-force-graph-2d` / D3.js (Force-directed physics simulation rendered on HTML5 Canvas)
*   **Metrics & Telemetry:** Recharts (Time-series path length, clustering, degree distributions)

---

## 🧭 Dashboard Navigation & Views

The dashboard is structured into two dedicated operator views:

### 1. Simulation Dashboard (`/` or `/simulation`) — Phase 2 Engine
Connects to the Python Flask mathematical simulation engine running on port 5001 (`app.py`):
*   **Real-Time Parameter Sliders:** Dynamically adjust $\alpha$ (Centrality Benefit), $\beta$ (Connection Cost), $\gamma$ (Social Similarity), and **$\delta$ (Proof-of-Throughput reward)** to observe emergent topology rewiring live.
*   **Adjacency Matrix Heatmap:** Live 2D array representation showing the emergence of the dense Core Hub in the top-left quadrant.
*   **Evolutionary Time-Series:** Live line charts tracking the decay of Average Path Length (APL) and exponential growth of the Clustering Coefficient across simulation ticks.
*   **Historical CSV Telemetry Export:** Fetch simulation step telemetry via `GET /api/results/export` for spreadsheet or LaTeX plotting.
*   **Journal Manuscript Assets (Member 2 Deliverables):** Publication-ready LaTeX markdown sections are available in [`docs/paper/`](file:///Users/mayankchauhan/Documents/SCOPE/docs/paper/) and vector graphics (`.pdf` / `.png`) in [`results/figures/`](file:///Users/mayankchauhan/Documents/SCOPE/results/figures/).

### 2. Network Dashboard (`/network`) — Phase 3 Physical Swarm
Connects to the C2 Tracker service running on port 5002 (`tracker.py`):
*   **Physical Swarm Force Graph:** Renders up to 75+ isolated Docker containers and their active physical TCP socket connections in real time.
*   **Node Inspector Panel:** Click any node in the canvas to view container metrics: physical container IP, degree, current bandwidth allocation, packet throughput, and defector state.
*   **Live P2P File Transfer:** Select a Source container and a Target container, click "Execute Transfer", and watch the packet trace traverse the physical TCP mesh hop-by-hop.
*   **Dynamic Adversarial Controls:** Click on any node to toggle its Defector status on-the-fly (turning an honest node into a Sybil Black Hole).
*   **Churn Resilience (Node Termination):** Send a `CONTROL_SHUTDOWN` command to kill a specific Docker container mid-simulation and observe honest nodes self-healing the topology.

---

## 📂 Frontend Architecture

```
frontend/
├── src/
│   ├── pages/
│   │   ├── SimulationDashboard.jsx   # Phase 2 Mathematical Simulation view
│   │   └── NetworkDashboard.jsx      # Phase 3 Physical Docker Swarm C2 view
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── NetworkGraph.jsx      # HTML5 Canvas force-directed D3 graph
│   │   │   ├── NodeInspector.jsx     # Side-drawer detailing selected node telemetry
│   │   │   ├── MetricsCharts.jsx     # Recharts time-series performance graphs
│   │   │   └── ControlPanel.jsx      # Parameter controls and execution buttons
│   │   └── ui/                       # Reusable Radix/Tailwind components
│   ├── hooks/
│   │   └── useSimulation.js          # Polling state hook keeping UI in sync with backend
│   ├── App.jsx                       # Navigation router and application layout
│   ├── main.jsx                      # React entry root
│   └── index.css                     # Design tokens, variables, and dark mode styling
├── package.json
└── vite.config.js
```

---

## 🛠️ Quick Start & Setup

### Prerequisites
*   Node.js (v18.0.0 or higher)
*   npm or yarn

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```
The application will launch on `http://localhost:5173`.

### 3. Connect Backends
*   For **Phase 2 (Simulation Dashboard)**: Ensure `python app.py` is running on `http://localhost:5001`.
*   For **Phase 3 (Network Dashboard)**: Ensure Docker Swarm is running (`docker compose up -d`) with Tracker on `http://localhost:5002`.

### 4. Build for Production
```bash
npm run build
```
Creates an optimized static bundle in `frontend/dist/`.
