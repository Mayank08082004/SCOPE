# SCOPE - Interactive React Dashboard

This is the official Web UI for the **SCOPE** P2P Network Simulation. It provides a real-time visualization of the network topology, dynamic charts for APL and Clustering metrics, and an interactive Node Inspector.

## 🚀 Built With
- **React.js** (Frontend library)
- **Vite** (Next-generation frontend tooling)
- **TailwindCSS** (Utility-first styling framework)
- **Shadcn/UI** & **Lucide React** (Component library & icons)
- **D3.js** (Network Force-Directed Graph visualization)
- **Recharts** (Time-series metrics charts)

## 🛠️ Quick Start

To run the dashboard locally, you must first have the Python Flask backend running.

1. Ensure your backend is running (`python app.py` from the root directory).
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.

## 📁 Key Components
* `ControlPanel.jsx`: Manages the backend connection to initialize and evolve the graph.
* `NetworkGraph.jsx`: Uses D3.js physics to render the live state of the P2P network.
* `NodeInspector.jsx`: Allows users to click on any node in the topology and inspect its underlying metrics (Degree, Bandwidth, Memory, Defector Status).
* `MetricsCharts.jsx`: Real-time Recharts rendering the optimization of APL, Clustering, and Degree Distribution.
