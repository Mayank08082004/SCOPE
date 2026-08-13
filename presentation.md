# SCOPE: Strategic Centrality-driven Overlay P2P Evolution
## Phase 3 Completion Presentation

### 1. The Vision
SCOPE was designed to model the self-organization of decentralized Peer-to-Peer (P2P) networks as a **Complex Adaptive System (CAS)**. Instead of a rigid, pre-defined topology, autonomous "Peer Agents" execute local OODA loops to optimize their connections based on a strategic utility function. 
The ultimate goal: **Evolve a random, unstructured network into a highly efficient, nested Core-Periphery Topology without central coordination.**

### 2. The Journey
*   **Phase 1:** Core mathematical theory and utility equations ($\alpha, \beta, \gamma$).
*   **Phase 2:** Massive scale array simulation using `Numba JIT` and `ProcessPoolExecutor`, alongside a React UI to visualize Graph Adjacency Matrices and Average Path Length (APL) decay.
*   **Phase 3 (Current):** Translating math into reality via a **Physical Docker Swarm**.

### 3. Phase 3 Achievements: The Physical Emulation
We successfully built and deployed a living, breathing network ecosystem:

#### 🐳 Dockerized Swarm Architecture
*   We transitioned from Python arrays to **75+ isolated Docker containers** running simultaneously.
*   Each container runs `node.py`, maintaining its own state, memory, and OODA loop thread.
*   Nodes communicate via real **Localhost TCP Sockets** using a custom binary-prefixed JSON protocol (`protocol.py`).

#### 🎛️ Real-Time C2 Dashboard
*   Built a highly-polished, Apple-esque Glassmorphism UI using React, Vite, and TailwindCSS.
*   Features a live, interactive `d3-force` network graph rendering all 75 physical containers and their active TCP socket connections in real-time.
*   Integrated **Command & Control (C2)** capabilities: Users can click on nodes in the physical graph to terminate instances (killing the Docker container's process) or toggle their Defector status on the fly.

#### 🕵️ Adversarial Modeling (The "Black Hole" Attack)
*   Introduced **Defector Nodes** to test network resilience.
*   Defectors launch Sybil-style attacks by spoofing their topological data (inflating their degree).
*   Honest nodes eagerly wire up to these Defectors, creating massive topological hubs that act as data black holes, silently dropping all intercepted file transfers.

#### 🚀 Live Routing & Bug Triage
*   Implemented live **P2P File Transfer Simulation** across the physical mesh.
*   Routing uses a greedy **Memory-Assisted Gradient Ascent** algorithm.
*   **Triage:** We identified and patched complex asynchronous networking bugs, including:
    *   Infinite routing loops (patched via path memory `n not in path`).
    *   Half-Duplex black holes (patched via spawning dedicated daemon threads for outbound socket reads).
    *   TCP Timeout thread death (patched by dynamically clearing timeouts post-handshake).

### 4. Theoretical Discoveries
*   **The Dead-End Phenomenon:** Through live simulation, we proved a fundamental limitation of greedy routing. Packets routed purely by Gradient Ascent can become trapped in local maximums (clusters of high-degree Hubs). If the target is in a different cluster, the packet exhausts all unvisited neighbors and hits a **FAILED_DEADEND**. This practically demonstrated why `self.memory` shortcuts and social clustering ($\gamma$) are vital for decentralized routing success.

### 5. Next Steps
SCOPE has proven that autonomous agents can self-organize physical TCP sockets into highly efficient topologies. Future work could involve introducing backtracking state-machines to resolve Dead-Ends, or porting `node.py` to WebRTC for browser-to-browser meshing.
