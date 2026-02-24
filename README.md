# SCOPE: Network Evolutionary Simulation

## Overview
SCOPE is a Python-based simulation project designed to model and analyze the evolutionary dynamics of networks. It focuses on how local agent behaviors (peer agents) influence global network properties such as routing efficiency (Average Path Length) and social clustering (Clustering Coefficient) over time.

## Project Structure
- `main.py`: The entry point for running the simulation. It executes the simulation, logs progress, and visualizes the final results.
- `src/`: Contains the core simulation logic.
  - `simulation.py`: Handles the initialization of the baseline network (Erdős–Rényi graph) and coordinates the evolutionary simulation steps involving agents.
  - `agent.py`: Defines the `PeerAgent` behavior, including observation and action strategies.
  - `config.py`: Contains configuration parameters for the simulation (e.g., number of nodes, initial degree, random seed, iterations, and rewiring probability).
- `requirements.txt`: Python package dependencies needed to run the simulation.

## Requirements
To install the dependencies, ensure you have Python installed, then run:

```bash
pip install -r requirements.txt
```

### Core Libraries
- `networkx`: For creating and analyzing complex networks.
- `matplotlib` & `seaborn`: For generating result visualizations.
- `numpy` & `pandas`: For numerical operations and data structuring.
- `tqdm`: For displaying simulation progress bars.

## Usage
To run the simulation and generate the visualizations, execute the `main.py` script from the project root:

```bash
python main.py
```

### Output
The simulation provides the following outputs:

1. **Console Output**: Displays the progress of the simulation and final network statistics (Final Average Path Length, Final Clustering Coefficient).
2. **Visualizations**: Displays a matplotlib window with three plots:
   - **Optimization of Routing Efficiency**: Tracks the average path length (hops) over simulation steps.
   - **Emergence of Social Clustering**: Tracks the clustering coefficient over simulation steps.
   - **Adjacency Matrix**: A heatmap representing the adjacency matrix of the top connected nodes sequentially ranked by their degree in the final graph.

## How it Works
1. **Initialization**: A baseline random Erdős–Rényi graph is created and configured to ensure complete connectivity.
2. **Evolution**: Over a configurable number of iterations, a subset of nodes (agents) is asynchronously activated.
3. **Agent Behavior**: Active agents observe their local environment and take actions that can rewire the network structure based on defined strategies.
4. **Metrics Tracking**: Global network metrics, specifically the Average Path Length and Clustering Coefficient, are recorded at each step to observe evolutionary trends.
