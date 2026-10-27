# SCOPE Remediation: Team Work Assignment & Sequential Execution Roadmap

> **Document Version:** 1.0  
> **Status:** Active Execution Plan  
> **Execution Model:** Sequential Relay Handover (Member 1 $\to$ Member 2 $\to$ Member 3)  
> **Target Journal:** *Peer-to-Peer Networking and Applications* (PPNA), Springer Nature  

---

## 1. Team Structure & Sequential Relay Pipeline

To ensure rigorous quality control and eliminate conflicting edits, work is structured as a **3-stage relay**. Each member completes and verifies their entire assignment before formally handing over the artifacts to the next member.

```
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 1: Mayank Chauhan (Lead Developer & Author 1)       │
│  Phase: Code Audit, Bug Fixes & Framework Enhancements      │
│  Deliverable: Tested, consistent codebase & metric engines  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                      [Formal Handover 1]
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 2: Samarth Dave (Author 2)                          │
│  Phase: Multi-Scale Simulations, Adversarial & Benchmarks   │
│  Deliverable: Empirical CSVs, benchmark data & figures      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                      [Formal Handover 2]
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 3: Miwa Dharod (Author 3)                           │
│  Phase: Mathematical Proofs, Manuscript & Overleaf LaTeX    │
│  Deliverable: Final corrected Springer Nature submission    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Member 1: Mayank Chauhan — Code Consistency & Bug Fixes

* **Role:** Lead Engineer & Corresponding Author (You)  
* **Focus:** Code logic, algorithm correctness, and framework instrumentation  
* **Target Files:**
  * `src/simulation.py`
  * `src/agent.py`
  * `src/config.py`
  * `src/network/node.py`
  * `tests/ablation_runner.py`

### Detailed Task Breakdown

#### Task 1.1: Fix Search Routing Early-Exit Bug
* **Location:** `src/simulation.py` (lines 135–149)
* **Problem:** If a target node is in `agent.memory` from prior gossip but is no longer a 2-hop neighbor, `bridge` evaluates to `None`. The code executes an unconditional `break`, causing the query to fail after only 1 hop instead of falling back to gradient ascent.
* **Fix:** Ensure that if `bridge is None`, the algorithm seamlessly falls back to gradient-ascent search instead of breaking.

#### Task 1.2: Fix Hysteresis Calculation for Signed/Negative Utilities
* **Location:** `src/agent.py` (lines 142 & 182)
* **Problem:** The condition `best_u > worst_u * 1.1` assumes strictly positive utility. When high degree penalty ($-\beta \cdot k_i/k_0$) drives utility negative, multiplying by $1.1$ reverses the inequality direction (e.g., $-2.1 > -2.2$ is true even though $-2.1$ is worse).
* **Fix:** Implement robust hysteresis:
  $$\Delta U = U_{\text{best}} - U_{\text{worst}} > \epsilon \cdot \max(0.01, |U_{\text{worst}}|)$$
  ensuring monotonicity and eliminating inverted swaps.

#### Task 1.3: Reconcile Betweenness Factor in Utility Function
* **Location:** `src/agent.py` (line 21) & `src/config.py`
* **Problem:** Code multiplies betweenness by `100.0` (`target_betweenness * 100.0`), while the paper formula specifies $\alpha [\ln(1+k_j) + \omega_B B_j]$.
* **Fix:** Align the multiplier cleanly and document the normalized scale $[0, 1]$ consistently between code and paper.

#### Task 1.4: Update TCP Prototype Utility Signature
* **Location:** `src/network/node.py` (lines 21–23, 293, 312)
* **Problem:** Physical Docker node calls `_jit_calculate_utility` with only 9 arguments, omitting `delta` and throughput. This caused physical nodes to operate with $\delta=0.0$.
* **Fix:** Update `node.py` to import `DELTA_WEIGHT` from `config.py` and pass estimated throughput into the utility calculation during live physical rewiring.

#### Task 1.5: Add Core-Periphery Quantitative Fit Metrics
* **Location:** `src/simulation.py` (`compute_metrics` function)
* **Problem:** Currently only computes APL and CC. Reviewer requires quantitative core-periphery emergence metrics (Issue B).
* **Fix:** Add automatic computation of:
  * Core size $|C|$ (nodes with $k \ge k_0$)
  * Degree assortativity coefficient $r = \text{nx.degree\_assortativity\_coefficient}(G)$
  * Borgatti-Everett Core-Periphery fit score

#### Task 1.6: Add Baseline Search Hop Tracking to Runner
* **Location:** `tests/ablation_runner.py` & `src/simulation.py`
* **Problem:** The runner only tracks final search hops, missing the baseline hop count needed for the 77% reduction comparison.
* **Fix:** Record `initial_search_hops` alongside `final_search_hops` in the output dictionary and CSV columns.

### Member 1 Completion & Handover Checklist
- [ ] All 6 code modifications implemented without regressions.
- [ ] Unit smoke test passed (`python -m tests.ablation_runner --quick` executes cleanly).
- [ ] Codebase committed and pushed to git repository.
- [ ] **Handover Document Prepared:** Confirming input/output signatures for Member 2.

---

## 3. Member 2: Samarth Dave — Multi-Scale Simulations, Adversarial Tests & Benchmarks

* **Role:** Simulation & Systems Lead (Author 2)  
* **Prerequisite:** Member 1 handover complete and verified.  
* **Target Files:**
  * `src/agent.py` & `src/simulation.py` (Adversarial models)
  * `tests/ablation_runner.py`
  * `tests/benchmark_prototype.py` (New physical benchmarking script)
  * `results/` (Output CSVs and figures)

### Detailed Task Breakdown

#### Task 2.1: Implement Multi-Strategy Adversarial Defector Suite
* **Problem:** Current evaluation only tests one naive defector type at 10% (Issue D).
* **Implementation:** Create 4 distinct attacker classes:
  1. *Type 1 (Naive Liar):* Inflates advertised degree ($3k+5$), drops 100% of packets ($T = 0.001$).
  2. *Type 2 (Intermittent Dropper):* Normal advertised degree, probabilistically drops 50% of forwarded traffic.
  3. *Type 3 (Colluding Sybil Cluster):* Defector clique falsely exchanging positive throughput ratings.
  4. *Type 4 (Sleeper Agent):* Honest behavior for first 10 iterations, defects after gaining hub status.
* **Experiments:** Run parameter sweeps across defector ratios: **5%, 10%, 20%, 30%**.

#### Task 2.2: Measure Adversarial Detection Accuracy
* Measure and log:
  * **False Positive Rate (FPR):** Honest peers mistakenly disconnected.
  * **False Negative Rate (FNR):** Malicious peers surviving in the core.
  * **Time-to-Isolation:** Number of OODA cycles until defector degree $k_d \to 0$.

#### Task 2.3: Generate Core-Periphery Emergence Empirical Data
* Run 20 independent Monte Carlo seeds using Member 1's new metrics engine.
* Record:
  * Assortativity coefficient $r$ (mean $\pm$ std).
  * Core size $|C|$ as fraction of total network.
  * Core-periphery fit score.
  * Emergence frequency across seeds (% of runs establishing stable core).

#### Task 2.4: Physical Docker Prototype Benchmarking
* **Problem:** Reviewer noted that "negligible CPU" and "zero socket hangs" were qualitative statements lacking numbers (Issue F).
* **Implementation:** Deploy container network (75, 100, 150 nodes) and benchmark:
  * End-to-end lookup latency (mean, median, 95th percentile in milliseconds).
  * CPU utilization per container under load (%).
  * Memory consumption per container (MB).
  * Socket message serialization and transfer overhead (messages/query).
  * Recovery time (seconds) after abrupt kill of 10% container population.

#### Task 2.5: Re-generate Publication Figures
* Update `results/ablation_summary.csv` and generate high-resolution PDF/PNG figures in `results/figures/`:
  * `fig1_apl_vs_delta.pdf`
  * `fig2_clustering_vs_gamma.pdf`
  * `fig3_hops_vs_alpha.pdf`
  * `fig4_throughput_vs_delta.pdf`
  * `fig5_adversarial_resilience.pdf` (New figure)
  * `fig6_prototype_scalability.pdf` (New figure)

### Member 2 Completion & Handover Checklist
- [ ] Multi-strategy adversarial simulation completed and CSVs saved.
- [ ] Core-periphery quantitative validation table generated.
- [ ] Prototype benchmark measurements recorded (latency, CPU, memory, overhead).
- [ ] All publication figures refreshed in `Springer_Paper/figures/`.
- [ ] **Handover Document Prepared:** Data package delivered to Member 3.

---

## 4. Member 3: Miwa Dharod — Theoretical Proofs, Paper Text & Overleaf Master

* **Role:** Formal Analysis & Manuscript Lead (Author 3)  
* **Prerequisite:** Member 2 handover complete with all datasets and tables.  
* **Target Files:**
  * `Springer_Paper/main.tex`
  * `Springer_Paper/COVER_LETTER.md` & `cover_letter.tex`
  * `Springer_Paper/MENTOR_SUBMISSION_AND_DEFENSE_GUIDE.md`

### Detailed Task Breakdown

#### Task 3.1: Repair Formal Convergence Proof (Appendix A.1 & A.2)
* **Problem:** Reviewer demonstrated that the telescoping sum $\oint \Delta \ln U = 0$ is invalid because peer utilities are interdependent, and the lower bound ignored $-\beta$ (Issue A).
* **Mathematical Revisions:**
  1. *Lemma 1 (Utility Bounds):* Formulate correct lower bound $U_{\min} = -\beta \frac{N-1}{k_0} + \delta \epsilon_T$ and establish the compact interval under the degree ceiling.
  2. *Lemma 2 (Acyclicity):* Replace the broken telescoping cycle argument with a **strict finite-state DAG acyclicity proof under bounded memory $M_i$**, demonstrating that the ordered sequence of unilateral improvements cannot re-visit states due to the positive hysteresis barrier $\epsilon > 0$.
  3. *Theorem 1:* Scope the $\epsilon$-Nash equilibrium precisely as a *bounded-memory pure-strategy $\epsilon$-Nash equilibrium*.

#### Task 3.2: Reframe Core-Periphery & Maintenance Cost ($\beta$)
* **Problem:** Proposition 2 was only an intuitive sketch (Issue B), and $\beta$ cancelled out of unilateral candidate comparison (Issue C).
* **Textual Revisions:**
  1. Reframe Proposition 2 to clearly state: *"Empirically observed and quantitatively verified core--periphery emergence under parameter regime $\mathcal{R}$"*, integrating Member 2's assortativity ($r$) and fit score data.
  2. Clarify in Section 3 and Section 5 that $\beta$ acts as a **systemic degree ceiling governor** ($k_{\max}$ bound in Proposition A.3) rather than a per-candidate local ranker, directly explaining why metric curves are flat across moderate $\beta$.

#### Task 3.3: Reconcile Headline Numbers & Multi-Scale Narrative (Issue E)
* Clarify the multi-scale hierarchy in the Abstract, Section 5, and Conclusion:
  * **Tier 1 (Ablation, $N=300$):** Baseline APL 4.30 $\to$ 2.48 (**42.35% reduction**), clustering 0.0100 $\to$ 0.3329 (33-fold increase).
  * **Tier 2 (Full-System Dynamic Churn, $N=500$):** Baseline APL 5.08 $\to$ 3.44 (**32.1% reduction**), baseline search hops 10.85 $\to$ 2.44 (**77% reduction**), clustering 0.0079 $\to$ 0.2552 (32-fold increase).
* Update Table 6 with explicit baseline search hop columns and confidence intervals.

#### Task 3.4: Integrate Physical Prototype Telemetry Table (Issue F)
* Insert a structured benchmark table in Section 5.4 containing Member 2's empirical prototype metrics:
  * End-to-end lookup latency (ms) across 75, 100, 150 containers.
  * Mean CPU and memory footprint per container.
  * Message overhead per query and churn recovery time (seconds).

#### Task 3.5: Final Overleaf / LaTeX Compilation & Submission Bundle
* Compile `Springer_Paper/main.tex` with `sn-jnl.cls` using pdflatex + bibtex.
* Ensure **0 compilation errors**, **0 warnings**, and complete citation resolution.
* Update `SCOPE_Springer_PPNA_Submission.zip` with refreshed figures, text, and bib entries.

### Member 3 Completion Checklist
- [ ] All 6 reviewer critiques addressed in formal LaTeX manuscript.
- [ ] Mathematical proofs verified for internal consistency.
- [ ] All numbers in Abstract, Tables, and Conclusion 100% synchronized.
- [ ] Cover letter updated to highlight rigorous theoretical and empirical revisions.
- [ ] Final compilation verified and zip bundle generated for Editorial Manager.

---

## 5. Execution Timeline & Next Action

| Stage | Responsible | Estimated Duration | Status |
|:---|:---|:---|:---|
| **Member 1 (Code & Engine Fixes)** | **Mayank Chauhan** | **1 – 2 Days** | **IN PROGRESS (Active)** |
| Handover 1 | Mayank $\to$ Samarth | Immediate upon tests passing | Pending |
| **Member 2 (Simulations & Benchmarks)** | **Samarth Dave** | **2 – 3 Days** | Queued |
| Handover 2 | Samarth $\to$ Miwa | Immediate upon CSV generation | Pending |
| **Member 3 (Proofs, Text & LaTeX)** | **Miwa Dharod** | **2 Days** | Queued |
| Final Verification & Mentor Review | All Authors + Prof. Sheetal | 1 Day | Queued |

---

> **Ready for Execution:**  
> We are now at **Member 1 (Mayank Chauhan)**. We will begin with **Task 1.1: Fixing the search early-exit bug in `src/simulation.py`**.
