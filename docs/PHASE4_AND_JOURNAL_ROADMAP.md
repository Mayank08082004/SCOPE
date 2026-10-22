# SCOPE: Phase 4 & Journal Publication Roadmap (3-Person Team Division)

This document outlines the strategic roadmap for completing **Phase 4 (Advanced Systems & Routing)**, preparing for the **End-Semester University Defense**, and drafting a submission-ready manuscript for an **Academic Journal** (e.g., *IEEE Transactions on Network and Service Management*, *Elsevier Computer Networks*, or *ACM Transactions on Autonomous and Adaptive Systems*).

---

## 👥 Team Work Breakdown (Logical Division for 3 Members)

To ensure all 3 team members can work **simultaneously without merge conflicts or code blocking**, responsibilities are cleanly decoupled along architectural boundaries:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               3-MEMBER WORK DECOUPLING                                 │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│ 👤 Member 1                │ 👤 Member 2                 │ 👤 Member 3                 │
│ Systems & Network Lead     │ Algorithmic & Theory Lead   │ Full-Stack UI & Paper Lead  │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ 📂 src/network/            │ 📂 src/ (Core Engine)       │ 📂 frontend/ & Manuscript   │
│ - Docker Swarm (node.py)   │ - agent.py & simulation.py  │ - React C2 Dashboard        │
│ - Backtracking Routing     │ - Utility function (δ term) │ - D3 Path Animations        │
│ - TCP Protocol Hardening   │ - Ablation Studies (N=5000) │ - LaTeX Journal Drafting    │
│ - Chaos/Resilience Tests   │ - Convergence Proofs        │ - Defense Slide Deck & Demo │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────┘
```

---

### 👤 Member 1: Distributed Systems & Network Engineering Lead
> **Ownership:** [`src/network/`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/), [`docker-compose.yml`](file:///Users/mayankchauhan/Documents/SCOPE/docker-compose.yml), [`Dockerfile`](file:///Users/mayankchauhan/Documents/SCOPE/Dockerfile)  
> **Git Branch:** `feature/distributed-routing-security`

#### Key Deliverables:
1.  **Backtracking State Machine in Physical Routing:**
    *   Upgrade `route_file_transfer()` in [`src/network/node.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/node.py).
    *   When a packet hits a dead-end (all neighbors visited in `path`), rather than immediately failing with `FAILED_DEADEND`, send a `BACKTRACK` signal to the previous hop to try the 2nd highest-degree neighbor.
    *   Target: Eliminate the dead-end failure mode completely; elevate physical swarm delivery success to >95%.
2.  **Distributed Telemetry & Betweenness Support:**
    *   Enhance [`src/network/tracker.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/tracker.py) to periodically compute sampled Betweenness Centrality across active edges and stream normalized betweenness scores back in heartbeat responses (`/api/tracker/heartbeat`).
    *   Feed this betweenness value into `node.py`'s JIT utility calculation (replacing the hardcoded `0.0`).
3.  **Physical Defector Quarantine & Verification:**
    *   Implement packet drop detection in `node.py`: when an honest node receives an unacknowledged file transfer via a peer, flag the peer's socket as suspicious.
    *   Test dynamic defector curing and churn tolerance under synthetic latency.
4.  **Transport Hardening:**
    *   Add an authorization token header for C2 commands (`KILL`, `TOGGLE_DEFECTOR`) in [`tracker.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/tracker.py) and `node.py` so arbitrary TCP sockets cannot terminate nodes.

---

### 👤 Member 2: Game Theory, Algorithms & Simulation Lead
> **Ownership:** [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py), [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py), [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py), [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py)  
> **Git Branch:** `feature/algorithmic-proofs-ablation`

#### Key Deliverables:
1.  **Bandwidth-Weighted Utility ($\delta$ Term) & Reputation:**
    *   Update the utility function in [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py):
        $$U_j = \alpha \ln(1 + k_j) - \beta \left(\frac{k_i}{10}\right) + \gamma S_{ij} + \delta \cdot T_{ij}$$
        Where $T_{ij}$ is measured historical throughput/delivery rate with peer $j$.
    *   If a defector node has high degree but zero throughput ($T_{ij} = 0$), $U_j$ drops drastically, causing honest agents to disconnect during their OODA `act()` step.
2.  **Engine Multiprocessing Cleanup:**
    *   Harmonize [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py): replace legacy `ProcessPoolExecutor` with the robust sequential Numba implementation used in [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py).
3.  **Massive Scale Ablation Studies for the Paper:**
    *   Execute automated sensitivity sweeps across varying parameter grids:
        *   $\alpha \in [0.5, 1.0, 2.0, 3.0]$ (Centrality impact)
        *   $\beta \in [0.2, 0.6, 1.0, 1.5]$ (Cost penalty impact)
        *   $\gamma \in [0.0, 0.5, 1.0, 2.0]$ (Clustering impact)
        *   $\text{Defector Ratio} \in [0\%, 5\%, 10\%, 20\%, 30\%]$
    *   Run benchmarks across 10 distinct random seeds ($N = 1,000$ and $N = 5,000$ nodes).
    *   Output vector graphs (PDF/EPS) and LaTeX tables with mean $\pm$ standard deviation for APL, Clustering, and Hop Counts.
4.  **Mathematical Convergence Analysis:**
    *   Write the formal Game Theory proof showing that the utility function defines a potential game that converges to a Nash Equilibrium (or $\epsilon$-stable Core-Periphery state).

---

### 👤 Member 3: Frontend C2, User Experience & Journal Manuscript Lead
> **Ownership:** [`frontend/`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/), Presentation Deliverables, Journal LaTeX Manuscript  
> **Git Branch:** `feature/ui-animation-journal-manuscript`

#### Key Deliverables:
1.  **Frontend Route Path Animation & Visual Polish:**
    *   In [`frontend/src/components/dashboard/NetworkGraph.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/components/dashboard/NetworkGraph.jsx), accept the active `path` from [`NetworkDashboard.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/pages/NetworkDashboard.jsx).
    *   Render an animated pulsing particle / glowing neon edge traveling hop-by-hop along the physical TCP path when a transfer is executed.
    *   Add smooth auto-centering / zoom-to-fit when a user selects a node in the inspector.
2.  **Journal Manuscript Management (Overleaf / LaTeX):**
    *   Set up the journal template (IEEE Transactions / Elsevier format).
    *   Author Sections:
        *   **Section 1: Introduction & Problem Statement** (Flooding vs DHT vs Complex Adaptive Systems).
        *   **Section 2: Related Work** (Chord, Kademlia, Gnutella, Core-Periphery networks, Tit-for-Tat).
        *   **Section 3: System Model & Architecture** (OODA Loop, Binary Framing, Overlay vs Underlay).
        *   Integrate mathematical formulations from Member 2 and system benchmarks from Member 1.
3.  **End-Semester Defense Preparation:**
    *   Build the master presentation slide deck using the 15-minute playbook from [`docs/presentation_and_demo.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/presentation_and_demo.md).
    *   Record a high-definition backup screen recording of the 75-node Docker Swarm executing live transfers and defectors (failsafe for live presentation day).
    *   Conduct mock defense grilling using [`docs/defense_qna_master.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/defense_qna_master.md).

---

## 🤝 Cross-Member Collaboration Matrix & Shared Files

While each member has primary code ownership to avoid blocking each other, several files and interfaces bridge between domains. Below is the **collaboration matrix**, detailing which members must coordinate, which files are shared, and the exact technical topics to discuss.

```
                  ┌───────────────────────────────┐
                  │           MEMBER 1            │
                  │   (Distributed & Sockets)     │
                  └───────┬───────────────▲───────┘
                          │               │
      Shared: src/config.py               Shared: src/network/tracker.py
      & _jit_calculate_utility            & /api/network/state
                          │               │
                          ▼               │
┌───────────────────────────┐             │
│         MEMBER 2          │             │
│    (Theory & Math)        │             │
└─────────────┬─────────────┘             │
              │                           │
              Shared: app.py & Paper Data │
              & Mathematical Notations    │
              │                           ▼
              └───────────────────►┌─────────────────────────────┐
                                   │          MEMBER 3           │
                                   │   (Frontend UI & Paper)     │
                                   └─────────────────────────────┘
```

---

### 1. 🔄 Member 1 (Systems) ⇄ Member 2 (Theory & Algorithms)

*   **Shared / Interface Files:**
    *   [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py) (Global weights: $\alpha, \beta, \gamma, \delta$, betweenness weight, defector ratio).
    *   [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py) (The JIT utility function `_jit_calculate_utility`).
    *   [`src/network/node.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/node.py) (Calls `_jit_calculate_utility` on line 21 and line 293).
*   **Critical Topics to Discuss:**
    1.  **Function Signature Contract (`_jit_calculate_utility`):**
        *   *The Risk:* Member 1's `node.py` directly imports `_jit_calculate_utility` from Member 2's `agent.py`. If Member 2 adds the new $\delta$ (throughput) parameter or changes argument order, Member 1's Docker containers will crash upon starting the OODA loop!
        *   *Agreement Needed:* Member 2 must inform Member 1 before changing the function signature. Default arguments or keyword parameters should be used so existing calls don't break.
    2.  **Betweenness Centrality Normalization:**
        *   *The Risk:* In `src/agent.py`, betweenness is multiplied by `100.0`. If Member 1's tracker computes betweenness on a different scale (e.g. $[0, 1]$ vs raw integer paths), utility scores will distort.
        *   *Agreement Needed:* Agree on the exact normalization scale (e.g., float between $0.0$ and $1.0$).
    3.  **Defector Telemetry & Drop Criteria:**
        *   *Agreement Needed:* Align how defector drop metrics are calculated. Member 2's simulation calculates drops at the algorithmic step level, while Member 1 measures drops via physical TCP packets. Ensure metric naming and formulas align.

---

### 2. 🔄 Member 1 (Systems) ⇄ Member 3 (Frontend C2 & Presentation)

*   **Shared / Interface Files & Endpoints:**
    *   [`src/network/tracker.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/tracker.py) (Flask API on port 5002).
    *   [`frontend/src/pages/NetworkDashboard.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/pages/NetworkDashboard.jsx) (Frontend consumer of tracker).
    *   [`frontend/src/components/dashboard/NetworkGraph.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/components/dashboard/NetworkGraph.jsx) (Canvas graph visualizer).
*   **Critical Topics to Discuss:**
    1.  **Transfer Path JSON Schema (For Canvas Animation):**
        *   *The Goal:* Member 3 wants to animate glowing particles hopping along the active transfer route on the D3 Canvas.
        *   *Agreement Needed:* Member 1 must ensure that `/api/tracker/transfer_status/<id>` returns an exact, ordered array of node IDs:
            ```json
            {
              "status": "SUCCESS",
              "path": ["node_1", "node_14", "node_42", "node_60"],
              "backtracks": [["node_14", "node_22"]] 
            }
            ```
            Member 3 must agree on this schema before building the React animation hook.
    2.  **C2 Authentication & Command Headers:**
        *   *Agreement Needed:* If Member 1 adds a secret token to protect `/api/tracker/control` (preventing rogue `KILL` commands), Member 1 must provide the token string so Member 3 can inject it into the frontend `fetch()` headers.
    3.  **Live Demo Rehearsal & Screen Recording:**
        *   *Agreement Needed:* Rehearse the physical demo sequence together: Member 1 boots the Docker swarm (`docker compose up -d`), while Member 3 screen-records the C2 dashboard executing transfers, defectors, and kills for the video backup.

---

### 3. 🔄 Member 2 (Theory) ⇄ Member 3 (Frontend & Journal Manuscript)

*   **Shared / Interface Files & Artifacts:**
    *   [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py) (Simulation backend on port 5001).
    *   [`frontend/src/pages/SimulationDashboard.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/pages/SimulationDashboard.jsx) & [`frontend/src/components/dashboard/ControlPanel.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/components/dashboard/ControlPanel.jsx).
    *   Journal Manuscript files (`docs/paper/` or Overleaf).
*   **Critical Topics to Discuss:**
    1.  **Simulation UI Parameter Sliders:**
        *   *The Goal:* Member 2 introduces the new $\delta$ parameter (proof-of-throughput) and configurable churn rates in `app.py`.
        *   *Agreement Needed:* Member 2 informs Member 3 of new `/api/config` fields so Member 3 can add matching sliders to `ControlPanel.jsx` in the React UI.
    2.  **Empirical Data & Vector Figures for the Journal:**
        *   *Agreement Needed:* Member 2 runs the ablation experiments ($N=1,000$ and $N=5,000$) and exports vector graphics (PDF/EPS) and raw CSV/LaTeX tables. Member 3 integrates them into the LaTeX document and authors the "Results & Discussion" analysis.
    3.  **Mathematical Notation Consistency:**
        *   *Agreement Needed:* Ensure identical symbols across the code, the React UI labels, and the journal text:
            *   $\alpha$ = Centrality Weight (`alpha`)
            *   $\beta$ = Maintenance Cost (`beta`)
            *   $\gamma$ = Social Similarity (`gamma`)
            *   $\delta$ = Proof-of-Throughput Weight (`delta`)
            *   $B(k)$ = Logistic Bandwidth (`bandwidth`)

---

### 4. 👥 All 3 Members: Team Synchronization Protocol

*   **Weekly 20-Minute Interface Sync (Every Monday):**
    *   Check if any function signatures or API JSON payloads need to change before coding.
*   **The "Zero-Broken-Dev" Integration Rule:**
    *   All feature branches are merged directly into `main` via a Pull Request reviewed by at least one other teammate.
    *   Before merging, run:
        1. `python app.py` (Verify math engine starts without error).
        2. `docker compose up -d` (Verify 75-node swarm starts without container crashes).
        3. `cd frontend && npm run build` (Verify frontend builds with zero syntax errors).

---

```
 Sprint 1 (Weeks 1-2)       Sprint 2 (Weeks 3-4)       Sprint 3 (Weeks 5-6)       Sprint 4 (Weeks 7-8)
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│  Algorithmic Core &  │──►│ System Integration & │──►│ End-Sem Defense &    │──►│ Journal Manuscript  │
│  Socket Backtracking │   │ Large-Scale Ablation │   │ Presentation Polish  │   │ Final Submission     │
└──────────────────────┘   └──────────────────────┘   └──────────────────────┘   └──────────────────────┘
```

### Sprint 1 (Weeks 1–2): Core Upgrades & Feature Branches
*   **Member 1:** Implement Backtracking logic in `src/network/node.py`; test hop recovery in a 5-node testbed.
*   **Member 2:** Add $\delta$ throughput validation to `src/agent.py`; harmonize `src/simulation.py` with sequential Numba.
*   **Member 3:** Implement D3 path animation on canvas; initialize IEEE LaTeX template on Overleaf.
*   *Milestone Checkpoint:* Merge all three branches into `main` with passing tests.

### Sprint 2 (Weeks 3–4): System Integration & Data Harvesting
*   **Member 1:** Deploy the Backtracking code to the 75-container Docker swarm; measure delivery success rate.
*   **Member 2:** Run parameter sensitivity sweeps ($N=1,000$ and $N=5,000$) across 10 random seeds; export LaTeX tables.
*   **Member 3:** Hook up route animation to live API in `NetworkDashboard.jsx`; draft Methodology & Architecture sections in paper.
*   *Milestone Checkpoint:* Swarm delivers >95% of packets without dead-ends; ablation data generated.

### Sprint 3 (Weeks 5–6): End-Semester Defense Execution
*   **Member 1:** Perform Churn & Node-Kill stability tests; verify Docker compose clean boots on presentation laptop.
*   **Member 2:** Finalize comparative plots (APL decay, Clustering S-curves, Logistic bandwidth distribution).
*   **Member 3:** Assemble final presentation slides; record demo backup video; conduct mock defense Q&A.
*   *Milestone Checkpoint:* **Ace the University End-Semester Project Defense.** 🎓

### Sprint 4 (Weeks 7–8): Journal Manuscript Finalization
*   **Member 1:** Write the Distributed Systems & Physical Socket implementation section.
*   **Member 2:** Write the Game Theory convergence proofs and experimental analysis section.
*   **Member 3:** Format citations (BibTeX), polish figures, perform editorial proofreading, and submit to journal portal.
*   *Milestone Checkpoint:* **Formal Journal Paper Submitted.** 📄

---

## 🔀 Git Branching Strategy & Coordination Rules

To prevent code collisions:

1.  **Protected Branch:**
    *   `main`: The only long-lived branch. All feature branches merge directly into `main` via Pull Requests once work for that phase is complete and verified.
2.  **Feature Branches (created off `main`, merged back into `main`):**
    *   `feature/distributed-routing-security` (Member 1)
    *   `feature/algorithmic-proofs-ablation` (Member 2)
    *   `feature/ui-animation-journal-manuscript` (Member 3)
3.  **Strict File Boundaries:**
    *   Member 1 only touches `src/network/`, `docker-compose.yml`, `Dockerfile`.
    *   Member 2 only touches `src/agent.py`, `src/config.py`, `src/simulation.py`, `app.py`.
    *   Member 3 only touches `frontend/` and `docs/paper/`.
    *   *If an interface change is needed (e.g. modifying packet JSON schema in `protocol.py`), all 3 members agree on the payload schema before editing.*

---

## 🎯 Target Journal Venues

| Venue | Publisher | Focus Area | Why SCOPE Fits |
| :--- | :--- | :--- | :--- |
| **IEEE Transactions on Network and Service Management (TNSM)** | IEEE | Decentralized routing, overlay management | Strong focus on both mathematical theory and physical testbed validation. |
| **Computer Networks** | Elsevier | Overlay architectures, P2P protocols, complex networks | Welcomes Complex Adaptive Systems (CAS) approaches to P2P network design. |
| **IEEE Communications Letters** | IEEE | Concise 4–5 page rapid publications | Ideal if submitting a shorter, high-impact paper focusing specifically on Core-Periphery routing emergence. |
