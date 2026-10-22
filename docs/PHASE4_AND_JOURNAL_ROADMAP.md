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

#### 🔗 Integration with Member 2's Completed Work (What Files to See & How to Use):
Member 2 has completed Phases A–D. Member 1 should inspect the following files to connect the physical swarm with the algorithmic engine:

*   **File 1: [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py) — `_jit_calculate_utility`**
    *   *Exact Signature:*
        ```python
        _jit_calculate_utility(
            target_degree, target_betweenness, my_degree,
            union_size, intersection_size,
            alpha, beta, gamma, bw_weight,
            delta=0.0, throughput=0.0
        )
        ```
    *   *Safety & Backward Compatibility:* `delta=0.0` and `throughput=0.0` default to zero. Existing calls in `src/network/node.py` (lines 293 and 312) will **NOT** break.
    *   *How Member 1 should use it in `node.py`:*
        1. Import `DELTA_WEIGHT` from `src.config`:
           ```python
           from src.config import ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT
           ```
        2. In `node.py` line 293, replace the 8-arg call with the full 10-arg call passing the peer's measured delivery throughput ($T_{ij} \in [0.0, 1.0]$):
           ```python
           peer_throughput = self.peer_delivery_success_rate.get(n, 1.0 if not self.is_suspicious(n) else 0.001)
           u = _jit_calculate_utility(
               float(target_degree), float(target_betweenness), float(my_degree),
               float(union_size), float(intersection_size),
               float(ALPHA), float(BETA), float(GAMMA), float(BETWEENNESS_WEIGHT),
               float(DELTA_WEIGHT), float(peer_throughput)
           )
           ```
    *   *Betweenness Normalization Contract:* In `_jit_calculate_utility`, betweenness is internally multiplied by `100.0` (`bw_weight * target_betweenness * 100.0`). Member 1's `tracker.py` must therefore pass normalized betweenness values in $[0.0, 1.0]$.
*   **File 2: [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py)**
    *   `DELTA_WEIGHT = 0.3` is defined and available for direct import.
*   **File 3: [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py)**
    *   Exposes `GET /api/config` and `POST /api/config` with `delta` and strict 400 validation. If Member 1 mirrors configuration between `tracker.py` and `app.py`, use the same JSON key schema (`delta`, `alpha`, `beta`, `gamma`, `betweenness_weight`, `defector_ratio`).

---

### 👤 Member 2: Game Theory, Algorithms & Simulation Lead
> **Ownership:** [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py), [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py), [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py), [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py), [`main.py`](file:///Users/mayankchauhan/Documents/SCOPE/main.py)  
> **Git Branch:** `feature/algorithmic-proofs-ablation`  
> **Status:** 🟢 **100% Completed** (Phases A, B, C, D Done & Tested; see [`docs/MEMBER2_PROGRESS_TRACKER.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/MEMBER2_PROGRESS_TRACKER.md))

#### Summary of Completed Deliverables:
1.  **Phase A (Utility & Simulation Cleanup):** Added $\delta \cdot T_{ij}$ term to `_jit_calculate_utility`; added `DELTA_WEIGHT = 0.3` to `src/config.py`; harmonized `src/simulation.py` with crash-free sequential Numba execution (removed problematic `ProcessPoolExecutor`).
2.  **Phase B (Ablation Experiments & Vector Graphics):** Created `tests/ablation_runner.py`; swept $\alpha, \beta, \gamma, \delta$ across 10 random seeds; produced publication-quality vector figures in `results/figures/` (`fig1`–`fig4` PDF+PNG) and CSV summaries in `results/`.
3.  **Phase C (Mathematical Proofs & Journal Sections):** Authored `docs/paper/theory_draft.md` (Lemma 4.1, Theorem 5.1, Corollary 6.1, Theorem 7.1), `docs/paper/journal_section_gametheory.md` (Section 4 IEEE style), and `docs/paper/journal_section_experiments.md` (Section 5 IEEE style).
4.  **Phase D (API Hardening & Batch CLI):** Hardened `app.py` with `delta` in `GET/POST /api/config` (400 validation), parallel step execution with `delta`, and new `GET /api/results/export` CSV download; upgraded `main.py` with full `argparse` CLI (`--delta`, `--nodes`, `--iterations`, `--seed`, `--no-plot`).

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
    *   Directly embed Member 2's completed paper sections, theorems, tables, and vector figures.
3.  **End-Semester Defense Preparation:**
    *   Build the master presentation slide deck using the 15-minute playbook from [`docs/presentation_and_demo.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/presentation_and_demo.md).
    *   Record a high-definition backup screen recording of the 75-node Docker Swarm executing live transfers and defectors (failsafe for live presentation day).
    *   Conduct mock defense grilling using [`docs/defense_qna_master.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/defense_qna_master.md).

#### 🔗 Integration with Member 2's Completed Work (What Files to See & How to Use):
Member 2 has delivered ready-to-use API endpoints, frontend interfaces, vector figures, and full journal sections:

*   **1. Frontend UI Changes (Simulation Dashboard):**
    *   *File to Edit:* [`frontend/src/components/dashboard/ControlPanel.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/components/dashboard/ControlPanel.jsx)
        *   `GET /api/config` from `app.py` now includes `'delta': 0.3`.
        *   `POST /api/config` accepts `{"delta": <float 0.0-2.0>}`.
        *   **Action for Member 3:** Add an input/slider for **$\delta$ (Proof-of-Throughput)** in `ControlPanel.jsx` alongside $\alpha, \beta, \gamma$. In `weightParams` state, initialize `delta: 0.3`. Add JSX:
            ```jsx
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium truncate" title="Proof-of-Throughput weight">δ (Throughput)</label>
              <Input type="number" name="delta" value={weightParams.delta || 0.3} onChange={handleWeightParamsChange} step="0.1" />
            </div>
            ```
    *   *File to Use:* [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py) — **`GET /api/results/export`**
        *   New CSV streaming endpoint. Returns `text/csv` with `step,apl,clustering_coefficient` headers.
        *   **Action for Member 3:** Add a "Download CSV" button in `ControlPanel.jsx` or `MetricsDisplay.jsx`:
            ```jsx
            <Button variant="outline" onClick={() => window.open('http://127.0.0.1:5001/api/results/export', '_blank')}>
              Export CSV
            </Button>
            ```
*   **2. Journal Manuscript Files (LaTeX / Overleaf Drop-Ins):**
    Member 2 has authored complete, publication-grade sections formatted in IEEE Transactions style:
    *   [`docs/paper/journal_section_gametheory.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/paper/journal_section_gametheory.md)  
        👉 **Drop directly into LaTeX as Section 4 (Game-Theoretic Framework & Convergence Analysis).** Contains Theorem 4.1 (PSNE existence via exact potential game), OODA convergence dynamics, Corollary 4.2 (Core-Periphery topology emergence), and Proposition 4.3 (Free-rider exclusion).
    *   [`docs/paper/journal_section_experiments.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/paper/journal_section_experiments.md)  
        👉 **Drop directly into LaTeX as Section 5 (Experimental Evaluation & Results).** Contains Table I ($\delta$ sweep), Table II ($\alpha$ sweep), Table III ($\gamma$ sweep), Table IV ($\beta$ sweep), comparative baseline table (SCOPE vs ER, BA, WS), and Section 5.7 reproducibility details.
    *   [`docs/paper/theory_draft.md`](file:///Users/mayankchauhan/Documents/SCOPE/docs/paper/theory_draft.md)  
        👉 **Drop into LaTeX as Appendix A (Formal Convergence Proofs & Bounds).** Contains detailed algebraic steps for Lemma 4.1 ($\Delta U_i = \Delta \Phi$), Theorem 5.1 (Finite Improvement Property), and Theorem 7.1 ($\Delta U_i^\delta < \delta$).
*   **3. Vector Figures for LaTeX (`\includegraphics`):**
    All figures are saved as vector PDF (recommended for LaTeX) and high-res PNG in [`results/figures/`](file:///Users/mayankchauhan/Documents/SCOPE/results/figures/):
    *   `fig1_apl_vs_delta.pdf` — Fig. 1: APL Reduction vs $\delta$
    *   `fig2_clustering_vs_gamma.pdf` — Fig. 2: Clustering Coefficient vs $\gamma$
    *   `fig3_hops_vs_alpha.pdf` — Fig. 3: Search Hops & Success Rate vs $\alpha$
    *   `fig4_throughput_vs_delta.pdf` — Fig. 4: Hub Bandwidth & BW Multiplier vs $\delta$
*   **4. Raw Data Tables:**
    *   [`results/ablation_summary.csv`](file:///Users/mayankchauhan/Documents/SCOPE/results/ablation_summary.csv) — Aggregated mean $\pm$ std dev across 10 random seeds per configuration.
    *   [`results/ablation_results.csv`](file:///Users/mayankchauhan/Documents/SCOPE/results/ablation_results.csv) — Raw individual seed data across all 40 parameter variations.

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
    *   [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py) (`DELTA_WEIGHT = 0.3` is defined and exported).
    *   [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py) (`_jit_calculate_utility` signature: `delta=0.0, throughput=0.0` optional kwargs).
    *   [`src/network/node.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/node.py) (Calls `_jit_calculate_utility` on line 21 and line 293).
*   **Final Interface Contracts & Agreement:**
    1.  **Function Signature Contract (`_jit_calculate_utility`):**
        *   *Status:* ✅ **Backward-compatible & Non-breaking.**
        *   Member 2 added `delta=0.0, throughput=0.0` with defaults at the end of the argument list.
        *   Member 1's existing 8-arg call in `node.py` continues to execute without crashing.
        *   When Member 1 activates Proof-of-Throughput in `node.py`, pass `float(DELTA_WEIGHT)` and measured `peer_throughput` ($\in [0.0, 1.0]$).
    2.  **Betweenness Centrality Normalization:**
        *   *Status:* ✅ **Contract Established.**
        *   In `_jit_calculate_utility`, betweenness is scaled as `bw_weight * target_betweenness * 100.0`.
        *   Member 1's `tracker.py` must normalize betweenness scores to the float range $[0.0, 1.0]$ before streaming to nodes.
    3.  **Defector Telemetry & Drop Criteria:**
        *   *Status:* ✅ **Aligned.**
        *   Member 2 proved in Theorem 7.1 that setting defector throughput $T_{ij} \approx 0$ isolates defectors. Member 1 should set $T_{ij} = 0.001$ for any peer with unacknowledged packet drops.

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
    *   [`frontend/src/components/dashboard/ControlPanel.jsx`](file:///Users/mayankchauhan/Documents/SCOPE/frontend/src/components/dashboard/ControlPanel.jsx) (Simulation parameter controls).
    *   Journal Manuscript files in [`docs/paper/`](file:///Users/mayankchauhan/Documents/SCOPE/docs/paper/).
    *   Publication figures in [`results/figures/`](file:///Users/mayankchauhan/Documents/SCOPE/results/figures/).
*   **Final Interface Contracts & Agreement:**
    1.  **Simulation UI Parameter Sliders & Endpoints:**
        *   *Status:* ✅ **Delivered in Phase D.**
        *   `GET /api/config` returns `{'delta': 0.3, ...}`.
        *   `POST /api/config` accepts `{'delta': <float 0.0-2.0>}` with HTTP 400 validation.
        *   `GET /api/results/export` streams full simulation history as CSV (`text/csv`).
        *   Member 3 adds $\delta$ slider in `ControlPanel.jsx` and optional "Export CSV" button.
    2.  **Empirical Data & Vector Figures for the Journal:**
        *   *Status:* ✅ **Delivered in Phase B & C.**
        *   Member 2 executed sweeps across 10 random seeds and generated PDF/PNG figures in `results/figures/` (`fig1` to `fig4`).
        *   Member 2 authored Section 4 (`docs/paper/journal_section_gametheory.md`), Section 5 (`docs/paper/journal_section_experiments.md`), and Appendix A (`docs/paper/theory_draft.md`).
        *   Member 3 imports these directly into the Overleaf LaTeX manuscript.
    3.  **Mathematical Notation Consistency:**
        *   $\alpha$ = Centrality Weight (`alpha`)
        *   $\beta$ = Maintenance Cost (`beta`)
        *   $\gamma$ = Social Similarity (`gamma`)
        *   $\delta$ = Proof-of-Throughput Weight (`delta`)
        *   $B(k)$ = Logistic Bandwidth (`bandwidth`)
        *   $\Phi(G)$ = Global Potential Function

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
