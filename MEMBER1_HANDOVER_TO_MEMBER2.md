# Formal Handover 1: Member 1 (Mayank Chauhan) $\to$ Member 2 (Samarth Dave)

> **Document Version:** 1.0  
> **Date:** October 27, 2026  
> **Status:** Completed & Verified  
> **Lead Developer (Member 1):** Mayank Chauhan (Author 1)  
> **Incoming Engineer (Member 2):** Samarth Dave (Author 2)  
> **Target Journal:** *Peer-to-Peer Networking and Applications* (PPNA), Springer Nature  

---

## 1. Executive Summary & Verification Status

Member 1 has completed all 6 mandated architectural and bug-fix remediation tasks in the SCOPE codebase. The entire execution suite has been validated via a 60-run ablation smoke test (`python3 -m tests.ablation_runner --quick`, covering 4 parameter sweeps across 3 independent Monte Carlo seeds at $N=500$ nodes), which completed with **zero errors, zero regressions, and full CSV/figure regeneration**.

| Task | Description | Status | Target Files | Verification |
|:---|:---|:---:|:---|:---|
| **1.1** | Fix Search Routing Early-Exit Bug | ✅ Done | `src/simulation.py`, `app.py` | Seamless fallback to gradient ascent verified |
| **1.2** | Robust Hysteresis for Signed/Negative Utilities | ✅ Done | `src/agent.py`, `src/network/node.py`, `src/config.py` | $\Delta U > \epsilon \cdot \max(0.01, \|U_{\text{worst}}\|)$ eliminates inverted swaps |
| **1.3** | Reconcile Betweenness Factor in Utility Function | ✅ Done | `src/agent.py`, `src/simulation.py`, `app.py` | Normalized $[0, 1]$ scale aligned; removed `* 100.0` |
| **1.4** | TCP Prototype Utility Signature Verification | ✅ Done | `src/network/node.py` | Live rewiring passes all 11 args ($\delta$ & throughput) |
| **1.5** | Core-Periphery Quantitative Fit Metrics Engine | ✅ Done | `src/simulation.py` | Borgatti-Everett discrete correlation + assortativity $r$ |
| **1.6** | Baseline Search Hop Tracking Engine | ✅ Done | `src/simulation.py`, `tests/ablation_runner.py` | `initial_search_hops` & `search_hop_reduction_pct` logged |

---

## 2. Detailed Code Modifications & API Signatures

### 2.1 Task 1.1: Search Routing Early-Exit Fix
* **Files:** [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py) & [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py)
* **Problem Solved:** When a query target was in `agent.memory` from prior gossip but was no longer reachable in 2 hops (`bridge is None`), the previous code executed an unconditional `break`, causing the query to abort after 1 hop instead of continuing.
* **New Implementation:** The loop only executes `break` if `bridge` is non-None. If `bridge is None`, execution falls through cleanly to step 2 (Gradient-Ascent degree-based routing).

### 2.2 Task 1.2: Robust Hysteresis for Signed Utilities
* **Files:** [`src/config.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/config.py), [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py), [`src/network/node.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/node.py)
* **Problem Solved:** The legacy condition `best_u > worst_u * 1.1` inverted swap decisions whenever utility became negative due to high maintenance costs ($-\beta \cdot k_i / k_0$).
* **New Implementation:** Defined `HYSTERESIS_EPSILON = 0.1` in `src/config.py`. Updated `PeerAgent.rewire()`, `PeerAgent.decide()`, and `Node.start_ooda_loop()` to enforce:
  $$\Delta U = U_{\text{best}} - U_{\text{worst}} > \epsilon \cdot \max(0.01, |U_{\text{worst}}|)$$
  This guarantees monotonicity and prevents cycling even under large negative baseline utilities.

### 2.3 Task 1.3: Betweenness Normalization & Formula Reconciliation
* **Files:** [`src/agent.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/agent.py), [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py), [`app.py`](file:///Users/mayankchauhan/Documents/SCOPE/app.py)
* **Problem Solved:** `agent.py` previously had a hardcoded `* 100.0` multiplier because raw NetworkX betweenness was unnormalized.
* **New Implementation:**
  1. `simulation.py` and `app.py` now normalize betweenness centrality scores to $[0.0, 1.0]$ via $B_j^{\text{norm}} = B_j / \max(B)$ before writing to graph node attributes.
  2. `src/agent.py` line 21 removes the artificial `* 100.0` scalar:
     $$\text{benefit} = \alpha \left[ \ln(1 + k_j) + \omega_B B_j^{\text{norm}} \right]$$
     matching Eq. (2) in `Springer_Paper/main.tex` exactly.

### 2.4 Task 1.4: TCP Prototype Live Utility Signature
* **Files:** [`src/network/node.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/network/node.py)
* **Verification:** `node.py` imports `ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT, HYSTERESIS_EPSILON` and calls `_jit_calculate_utility` with the full 11-argument signature during both neighbor pruning and candidate evaluation.

### 2.5 Task 1.5: Core-Periphery Quantitative Engine
* **Files:** [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py)
* **New Function:**
  ```python
  def compute_core_periphery_metrics(G, k0=10) -> dict
  ```
  Returns:
  * `'core_size'`: Count of core nodes $|C| = |\{i \in V : k_i \ge k_0\}|$
  * `'core_fraction'`: Core fraction $|C| / N$
  * `'assortativity'`: Newman degree assortativity coefficient $r \in [-1, 1]$
  * `'cp_fit_score'`: Borgatti & Everett (1999) Pearson correlation $\rho = \text{corr}(A, \Delta)$ between empirical adjacency $A$ and ideal core-periphery matrix $\Delta$ ($\Delta_{ij} = 1$ if $i \in C \lor j \in C$, $0$ otherwise).
* **Backward Compatibility:** `compute_metrics(G, include_cp=False)` retains its signature returning `(apl, cc)` for existing callers, but accepts `include_cp=True` to return `(apl, cc, cp_dict)`.

### 2.6 Task 1.6: Baseline Hop Count Tracking
* **Files:** [`src/simulation.py`](file:///Users/mayankchauhan/Documents/SCOPE/src/simulation.py), [`tests/ablation_runner.py`](file:///Users/mayankchauhan/Documents/SCOPE/tests/ablation_runner.py)
* **New Implementation:** `run_simulation_parameterized()` evaluates 50 search queries on the initial random graph prior to evolution (`initial_search_hops`, `initial_search_success_pct`) and computes `search_hop_reduction_pct = (initial - final) / initial * 100`.
* **Output Dict & CSV Columns:**
  * `initial_search_hops`
  * `final_search_hops`
  * `search_hop_reduction_pct`
  * `core_size`, `core_fraction`, `assortativity`, `cp_fit_score`

---

## 3. Verified Smoke Test Baseline Metrics ($N=500$, Quick Sweep)

From `results/ablation_summary.csv` (Baseline $\alpha=2.0, \beta=0.6, \gamma=1.0, \delta=0.3$):
* **APL:** Initial $4.73 \to$ Final **$2.68 \pm 0.09$** (**$+43.40\% \pm 3.13\%$ reduction**)
* **Clustering Coefficient:** Initial $0.008 \to$ Final **$0.2925 \pm 0.0190$** (**36-fold increase**)
* **Search Hops:** Baseline Initial **$10.82 \pm 0.92$** $\to$ Converged **$3.40 \pm 0.32$** (**$68.33\% \pm 5.00\%$ reduction**)
* **Search Success Rate:** $56.7\% \pm 8.1\%$
* **Bandwidth Multiplier:** **$11.22\times \pm 6.30\times$**
* **Core Size $|C|$ ($k \ge 10$):** **$36.33 \pm 2.31$ nodes** ($7.27\% \pm 0.46\%$ of overlay)
* **Degree Assortativity ($r$):** **$-0.4129 \pm 0.0320$** (disassortative star/hub topology)
* **Borgatti-Everett CP Fit ($\rho$):** **$0.2078 \pm 0.0051$** (positive core-periphery correlation)

---

## 4. Specific Action Items & Interfaces for Member 2 (Samarth Dave)

You may now take over the execution relay. Here are the exact entry points and specifications for your tasks:

### Task 2.1 & 2.2: Adversarial Defector Suite & Detection Accuracy
1. **Location:** Implement attacker classes in `src/agent.py` inheriting from `PeerAgent` or parameterizing `PeerAgent`:
   * **Type 1 (Naive Liar):** Advertises degree $3k + 5$, throughput $T = 0.001$.
   * **Type 2 (Intermittent Dropper):** Advertises truthful degree, drops 50% packets probabilistically ($T \approx 0.5$).
   * **Type 3 (Colluding Sybil Cluster):** Sybil clique exchanging maximum throughput ratings with each other.
   * **Type 4 (Sleeper Agent):** Behaves honestly for first 10 OODA steps, defects after acquiring degree $\ge 10$.
2. **Defector Ratios:** Run sweeps across $5\%, 10\%, 20\%, 30\%$ defector population.
3. **Log Metrics:**
   * False Positive Rate (FPR): Honest nodes with pruned links / total honest nodes.
   * False Negative Rate (FNR): Malicious nodes retained in core / total malicious nodes.
   * Time-to-Isolation: Mean OODA iterations until defector degree $k_d \to 0$.

### Task 2.3: Quantitative Core-Periphery Monte Carlo Data
1. Run 20 independent seeds using `run_simulation_parameterized()` or direct calls to `compute_core_periphery_metrics(G)`.
2. Extract `assortativity` ($r$), `core_size`, `core_fraction`, and `cp_fit_score`.
3. Tabulate the emergence frequency (% of seeds where $\rho > 0.15$ and $|C| > 0$).

### Task 2.4: Physical Docker Prototype Benchmarking
1. Script `tests/benchmark_prototype.py` to deploy and query Docker container overlays at 75, 100, and 150 nodes.
2. Measure and log:
   * End-to-end lookup latency (ms: mean, median, 95th percentile).
   * CPU (%) and memory (MB) per container using `docker stats`.
   * Message overhead (TCP frames per query).
   * Churn recovery latency (seconds to re-stabilize after 10% node kill).

### Task 2.5: Re-generate Publication Figures
1. Execute full ablation run (`python3 -m tests.ablation_runner` with 10 seeds at $N=5000$).
2. Refresh all PDF/PNG figures in `results/figures/` and copy the final publication figures into `Springer_Paper/figures/` for Member 3.

---

> **Handover Signoff:**  
> **Member 1 (Mayank Chauhan):** Completed, tested, and ready for Member 2.  
> **Repository Commit:** Verified clean working tree.
