# SCOPE — Reviewer Critique: Comprehensive Remediation Plan

> **Status:** PLAN ONLY — No files have been modified yet.
> **Scope:** All 6 major critique areas from the external reviewer analysis.
> **Target Journal:** *Peer-to-Peer Networking and Applications* (PPNA), Springer Nature

---

## Overview of Issues

| # | Issue | Location in Paper | Severity |
|---|-------|-------------------|----------|
| A | Convergence proof is logically incomplete | Section 4.2 + Appendix A.1–A.2 | 🔴 Critical |
| B | Core-periphery emergence not quantitatively proven | Section 4.3 / Proposition 2 | 🟠 Major |
| C | β parameter appears to have no effect on candidate ranking | Section 3 / Table 5 | 🟠 Major |
| D | Free-rider adversarial testing too narrow | Section 5 + Proposition 3 | 🟠 Major |
| E | Headline metrics are internally inconsistent | Abstract, Conclusion, Tables | 🔴 Critical |
| F | Prototype has no quantitative performance measurements | Section 5.4 | 🟡 Moderate |

---

## Issue A — Convergence Proof: The Telescoping Argument is Broken

### What the reviewer said
> *"Improving one peer's utility does not necessarily improve a common global potential function. The utilities of other peers may change when an edge is rewired. Consequently, the claimed telescoping argument does not follow from the stated assumptions."*

### What is currently in the paper
In **Appendix A.2 (Lemma 2 — Acyclicity)**, the proof sums logarithmic utility increments along a cycle and claims:

$$\oint_{\text{cycle}} \Delta \ln U = 0$$

because "every link added is identically removed."

The problem: when agent $i$ swaps link $(i,j)$ for $(i,k)$, the utilities of $j$, $k$, and all their mutual neighbors **also change** (Jaccard similarity terms change, degrees change from their perspective, etc.). So the "cycle closes to zero" claim is only valid if utility is a function of a single agent in isolation — but it is not. The utilities are mutually dependent across peers.

Additionally, in **Appendix A.1 (Lemma 1)**, the stated lower bound is:

$$U_{\min} \equiv \delta \cdot \epsilon_T > 0$$

But the full utility function includes a subtracted term $-\beta(k_i/k_0)$, which can be large for high-degree nodes. So $U_{\min} = \delta \cdot \epsilon_T$ is incorrect — it ignores the negative term.

### What needs to change

#### Fix 1 — Correct the lower bound in Appendix A.1
The correct lower bound must account for the negative maintenance term:

$$U_{\min} = -\beta \cdot \frac{N-1}{k_0} + \delta \cdot \epsilon_T$$

This can be negative for high-degree nodes. Two resolution options:
- **(Option A)** Re-interpret $U_i(j)$ as a *relative* utility used only for ranking candidates (not as an absolute positive value). The hysteresis condition uses a ratio, and the ratio condition still excludes cycles regardless of the sign.
- **(Option B)** Restrict $U_{\min} > 0$ to the regime $k_i < k_0 \cdot \delta\epsilon_T / \beta$ and note that this is always satisfied at equilibrium given the degree ceiling from Proposition A.3.

#### Fix 2 — Replace the telescoping cycle argument in Appendix A.2
The current argument assumes individual utilities telescope to zero around a cycle. This is only valid if utilities are **exact potential functions**. The correct approach is to define a global potential function $\Phi(G)$ that strictly increases after every accepted rewiring step and is bounded above. A natural candidate:

$$\Phi(G) = \sum_{i \in V} \sum_{j \in \mathcal{N}_i} U_i(j)$$

Show that the sum of all pairwise utilities across the current edge set strictly increases after every swap, accounting for the effect on both $i$'s neighbors and the neighbors' views of their own links.

Alternatively, use a **finite-state DAG argument**: The state space $\mathcal{G}_N$ is finite, and if a monotone invariant (any quantity that strictly changes with each move) can be found, acyclicity follows. A clean monotone invariant exists: the ordered pair $(U_i(k^*), U_i(j^*))$ for the activating agent strictly changes in a provably non-reversible way under $\epsilon > 0$.

#### Fix 3 — Clarify the equilibrium definition
Specify that the $\epsilon$-Nash equilibrium is defined with respect to **unilateral deviations within the bounded candidate memory $M_i$**, not all possible deviations in $\mathcal{G}_N$. This is a weaker but honest and realistic definition — label it *bounded-rationality $\epsilon$-Nash equilibrium*.

### Sub-task Table
| Sub-task | Where | Action |
|----------|-------|--------|
| A1 | Appendix A.1, Equation for $U_{\min}$ | Rewrite lower bound to include the negative maintenance cost; state conditions under which $U_{\min}$ is positive |
| A2 | Appendix A.2, Lemma 2 proof body | Replace telescoping cycle argument with a valid monotone-invariant or potential-function argument |
| A3 | Section 4.2, Theorem 1 proof | Add clarification that equilibrium deviations are scoped to candidate memory $M_i$ |
| A4 | Abstract / Conclusion | Soften to "we establish convergence under bounded candidate memory" — do not claim fully proven |

---

## Issue B — Core-Periphery Emergence: Proof Sketch vs. Guarantee

### What the reviewer said
> *"Proposition 2 claims that decentralized utility maximization produces a nested core–periphery topology. The proof sketch describes plausible forces but does not establish that every equilibrium must have the claimed structure."*

### What is currently in the paper
**Proposition 2 (Section 4.3)** gives a proof sketch listing three forces (hub formation, degree saturation, triadic closure) but states no quantitative conditions under which these forces *necessarily* produce a core-periphery topology. The conclusion "Together, these forces self-organize the network..." is intuitive, not proven.

### What needs to change

#### Fix 1 — Clearly label the claim
Downgrade from a formal mathematical proposition to a *structural observation* or *empirically supported claim*:
> *"Empirically, across all Monte Carlo trials, the SCOPE overlay consistently converges to a nested core-periphery configuration as measured by [metric]. We provide a proof sketch of the key structural forces and empirical validation."*

#### Fix 2 — Add quantitative core-periphery measurement
Report the following metrics in the results tables:
- **Core size** $|C|$ — fraction of nodes with degree $k \geq k_0$
- **Degree assortativity** $r$ — Newman's formula; positive $r$ indicates hub-hub clustering
- **Core-periphery fit score** — Borgatti-Everett correlation between empirical adjacency and ideal CP adjacency matrix
- **Frequency of CP emergence** — e.g., "38 of 50 trials converged to $r > 0.4$"

#### Fix 3 — State the exact conditions
Characterize parameter regimes under which CP emergence is observed vs. not (e.g., what happens when $\gamma = 0$?). This can be extracted from existing Table 3 (the $\gamma$ sweep).

### Sub-task Table
| Sub-task | Where | Action |
|----------|-------|--------|
| B1 | Proposition 2 label | Change to "Observation" or add "Empirically Supported" qualifier |
| B2 | Results Section 5.2 | Add CP quantitative metrics table (core size, assortativity, CP fit score, emergence frequency) |
| B3 | Proof sketch | Explicitly state conditions needed for each force to dominate, mapped to parameter ranges |

---

## Issue C — The β Parameter Does Not Affect Candidate Ranking

### What the reviewer said
> *"The rewiring operation preserves the acting peer's degree. Therefore, the maintenance cost term is constant when the peer compares candidate neighbors. Table 5 confirms metrics remain identical for β=0.1, 0.3, 0.6, 0.9."*

### What is currently in the paper
The utility function:
$$U_i(j) = \alpha[\ln(1+k_j) + \omega_B B_j] - \beta(k_i/k_0) + \gamma S_{ij} + \delta T_{ij}$$

When agent $i$ compares candidates $j$ and $k$, the term $-\beta(k_i/k_0)$ is **identical for both** (since $k_i$ is unchanged during comparison). So $\beta$ cancels out and has **no effect on which candidate wins**. Table 5's finding of no change across β = 0.1, 0.3, 0.6, 0.9 is therefore mathematically expected — not a validation.

### What needs to change

#### Option 1 — Reinterpret β's role honestly (Recommended)
State clearly that $\beta$ is not a per-candidate ranking parameter, but a **global overlay health constraint**. It affects the **degree ceiling** in Appendix A.3 (Proposition A.3):

$$k_{\max} \leq k_0 \cdot \frac{\alpha + \gamma + \delta}{\beta}$$

Show empirically that as $\beta$ increases, equilibrium hub degree distributions shift downward. Report hub degree distributions across the $\beta$ sweep.

#### Option 2 — Modify the utility function (more involved)
Change the cost term to depend on the **candidate's degree** $k_j$, not $k_i$:
$$U_i(j) = \alpha[\ln(1+k_j) + \omega_B B_j] - \beta(k_j/k_0) + \gamma S_{ij} + \delta T_{ij}$$
This models the cost of connecting to a high-degree hub. Under this formulation, $\beta$ genuinely differentiates candidates and its sensitivity would appear in experiments. **This requires simulation re-runs.**

> **Recommendation:** Option 1 is safer (no re-runs). Option 2 is stronger but costly.

### Sub-task Table
| Sub-task | Where | Action |
|----------|-------|--------|
| C1 | Section 3.2 (Utility Function) | Add clarification that $\beta(k_i/k_0)$ is constant during unilateral comparison — it acts as a global degree regulator |
| C2 | Table 5 discussion | Reframe: "Invariance of metrics across $\beta$ is mathematically expected; $\beta$'s role is in the degree ceiling bound (Proposition A.3), not candidate selection" |
| C3 | Appendix A.3 | Verify that equilibrium hub degree distributions shift as $\beta$ increases |

---

## Issue D — Free-Rider Suppression: Too Narrow an Adversarial Model

### What the reviewer said
> *"It tests a narrow attacker model. It does not establish resilience to colluding peers, intermittent packet dropping, manipulated throughput measurements or strategic attackers that behave honestly until selected."*

### What is currently in the paper
- Only **one adversary type**: advertise inflated degree + drop all packets ($T_{id} = \epsilon_T = 0.001$)
- Only **one adversary fraction**: 10%
- No false-positive or false-negative rates reported

### What needs to change

#### Fix 1 — Add multiple adversary strategies

| Attacker Type | Behavior | Detection Difficulty |
|---------------|----------|---------------------|
| Type 1 (current) | Inflated degree + zero throughput | Easy |
| Type 2 — Intermittent | Drops 50% of packets randomly | Medium |
| Type 3 — Colluding Sybil | Group of dishonest peers vouch for each other | Hard |
| Type 4 — Sleeper | Honest until selected as relay, then drops | Very hard |

#### Fix 2 — Vary adversary fraction
Test at: 5%, 10%, 20%, 30%. Report whether SCOPE remains stable above a threshold.

#### Fix 3 — Report detection accuracy
For each adversary type and fraction, report:
- **False positive rate** — honest peers incorrectly dropped
- **False negative rate** — defectors that survive pruning
- **Time-to-detection** — iterations until defectors are isolated

#### Fix 4 — Compare with a baseline
Compare SCOPE's defector exclusion against a naive mechanism (random neighbor replacement) and a known scheme (EigenTrust or tit-for-tat).

#### Fix 5 — Clarify throughput signal trust model
State explicitly whether SCOPE assumes trusted or adversarial throughput signals, and what happens when signals are fabricated.

### Sub-task Table
| Sub-task | Where | Action |
|----------|-------|--------|
| D1 | Section 5 (Adversarial Eval.) | Add 3+ attacker types in a structured table |
| D2 | Section 5 | Report adversary fraction sweep (5%, 10%, 20%, 30%) |
| D3 | Section 5 | Add false-positive/false-negative rates and time-to-detection |
| D4 | Section 5 | Add comparison to EigenTrust or tit-for-tat as baseline |
| D5 | Section 3 | Add sentence on whether throughput signals are self-reported or independently verified |

---

## Issue E — Headline Metrics Are Internally Inconsistent

### What the reviewer said
> *"Table 6 reports APL of 4.30 for E-R baseline and 2.48 for SCOPE — that is a 42.3% reduction, not 32.1%. The 77% search-hop claim requires an explicitly reported baseline hop count."*

### What is currently in the paper
- **Abstract & Conclusion claim:** "32.1% reduction in average path length"
- **Table 6 data:** Baseline APL = 4.30, SCOPE APL = 2.48 → actual = $(4.30 - 2.48)/4.30 = 42.3\%$
- **Abstract & Conclusion claim:** "77% reduction in search hops" — no explicit baseline hop count provided
- **Search success rate** in tables: 40–54%, which looks contradictory with "77% hop reduction"

### What needs to change

#### Fix 1 — Reconcile the 32.1% figure
Either:
- If 32.1% comes from the N=300 ablation (not N=500), make this explicit in the abstract.
- If it is simply wrong, correct to 42.3% everywhere.

#### Fix 2 — Add explicit baseline hop count for the 77% claim
Add a results row: "Under E-R baseline, gradient-ascent averaged $H_{\text{baseline}}$ hops per successful query. Under SCOPE: $H_{\text{SCOPE}}$, a reduction of 77%."

#### Fix 3 — Separate the three experimental tiers in the abstract
Clarify which tier (N=300 ablation, N=500 simulation, Docker) each headline metric originates from.

#### Fix 4 — Add confidence intervals and statistical tests
Every headline metric must include: mean ± std, number of Monte Carlo trials, and statistical significance (e.g., Welch's t-test p-value).

#### Fix 5 — Reconcile search success rate with hop reduction
Explain clearly: "77% hop reduction" refers to hops-per-successful-query; 40–54% is the search success rate (TTL-limited). These are distinct metrics. Add a table separating:
- Search success rate (%)
- Mean hops per *successful* query
- Mean hops per *attempted* query
- Message overhead per query

### Sub-task Table
| Sub-task | Where | Action |
|----------|-------|--------|
| E1 | Abstract (line ~69) | Verify and correct the 32.1% figure — trace which table it comes from |
| E2 | Conclusion (line ~636) | Align all claimed percentages with corresponding table rows |
| E3 | Table 6 discussion | Add explicit baseline hop count for the 77% claim |
| E4 | All results tables | Add confidence intervals and number of Monte Carlo trials |
| E5 | Results section | Add a unified summary table labeling which tier each metric belongs to |

---

## Issue F — Prototype Has No Quantitative Performance Data

### What the reviewer said
> *"'Negligible CPU utilization' and 'robust operation' need measurements. Report latency, message overhead, CPU/memory as peer count increases."*

### What is currently in the paper
Section 5.4 contains only qualitative claims:
- "more than 75 Docker containers"
- "negligible CPU utilization and zero socket hangs"
- No latency, no memory figures, no throughput numbers

### What needs to change

#### Add a quantitative prototype results table

| Metric | Value |
|--------|-------|
| End-to-end lookup latency (mean ± std) | ? ms |
| Message overhead per query | ? messages/query |
| CPU utilization per container (idle / under load) | ?% / ?% |
| Memory per container | ? MB |
| OODA rewiring handshake round-trip time | ? ms |
| Recovery time after 10% churn event | ? seconds |
| Concurrent queries handled | ? queries/sec |
| Container count tested | 75, 100, 150 |

#### At minimum — remove unsubstantiated qualitative claims
If measurements cannot be run, replace "negligible CPU utilization" with "qualitative observation; quantitative profiling is reserved for future work." This is honest and avoids a reviewer flag.

### Sub-task Table
| Sub-task | Where | Action |
|----------|-------|--------|
| F1 | Section 5.4 | Add quantitative metrics table from prototype benchmarks |
| F2 | Section 5.4 | Replace "negligible CPU utilization" with measured values or scope to future work |
| F3 | Section 5.4 | Show performance at 75, 100, 150 peer counts to demonstrate scaling |

---

## Summary: Prioritized Execution Order

```
Priority 1 — Do FIRST (Blocks journal review credibility)
  ├── E: Fix all headline metric inconsistencies (abstract, conclusion, tables)
  └── A: Fix the convergence proof (Appendix A.1 and A.2)

Priority 2 — Do SECOND (Major technical depth)
  ├── C: Clarify β's role honestly in the paper text
  └── B: Add quantitative CP emergence metrics (requires a new table)

Priority 3 — Do THIRD (Strengthens experimental sections)
  ├── D: Expand adversarial evaluation (multiple attacker types, fractions)
  └── F: Add prototype performance measurements
```

---

## Effort Estimates

| Issue | Writing Effort | Simulation Needed? | Estimated Time |
|-------|---------------|-------------------|----------------|
| A | Medium — rewrite 2 proofs | No | 2–3 hours |
| B | Medium — add metrics table + relabel proposition | Yes (small) | 3–4 hours |
| C | Low — clarify text + one new table column | Yes (small) | 1–2 hours |
| D | High — design 3+ attacker types + run experiments | Yes (major) | 1–2 days |
| E | Low — arithmetic corrections + CI reporting | No | 1–2 hours |
| F | High — benchmark Docker prototype | Yes (major) | 1–2 days |

---

> **This plan is complete and ready for execution. No files have been modified. Await your confirmation before implementing any change.**
