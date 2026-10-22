# SCOPE: Game Theory Journal Section
## Section 4 — Game-Theoretic Framework & Convergence Analysis

> **Author:** Member 2 — Game Theory, Algorithms & Simulation Lead
> **Format:** LaTeX-convertible Markdown (IEEE Transactions style)
> **Status:** 🟢 Complete (Phase C — Task C5)
> **Hand-off:** Member 3 → drop into LaTeX template as Section 4

---

## 4. Game-Theoretic Framework

### 4.1 Problem Formulation

We model the SCOPE peer-to-peer overlay network as a *strategic network formation game* [Jackson & Wolinsky, 1996]. Each of the $N$ autonomous agents simultaneously and repeatedly selects which overlay connections to maintain, aiming to maximise a private utility that balances three competing objectives: routing efficiency, bandwidth incentive alignment, and social clustering.

**Formal game definition.** The game is a tuple $\Gamma = (V, \{\mathcal{S}_i\}_{i \in V}, \{U_i\}_{i \in V})$ where:

- $V = \{1, \ldots, N\}$ is the finite set of peer agents.
- $\mathcal{S}_i = D_i \times A_i$ is agent $i$'s strategy space: the Cartesian product of a *drop-set* (edges eligible to remove) and an *add-set* (candidate edges to form), drawn from bounded gossip memory $M_i$ ($|M_i| \leq 100$).
- $U_i : \mathcal{S}_i \times \mathcal{S}_{-i} \to \mathbb{R}$ is agent $i$'s utility function.

**The null action** (retain all edges) is always available, ensuring $\mathcal{S}_i \neq \emptyset$ for all $i$.

### 4.2 The SCOPE Utility Function

The utility for agent $i$ connecting to peer $j$ is:

$$
U_i(j) = \underbrace{\alpha \!\left[\ln(1 + k_j) + \omega_B \cdot B_j^{\text{norm}}\right]}_{\text{Centrality Benefit}}
         -\underbrace{\beta \cdot \frac{k_i}{10}}_{\text{Maintenance Cost}}
         +\underbrace{\gamma \cdot S_{ij}}_{\text{Social Similarity}}
         +\underbrace{\delta \cdot T_{ij}}_{\text{Proof-of-Throughput}}
\tag{1}
$$

**Term-by-term analysis:**

**Centrality Benefit $[\alpha]$:** The logarithmic degree term $\alpha \ln(1+k_j)$ encodes a diminishing-returns preference for high-degree hub nodes. This reflects empirical findings from Barabasi-Albert preferential attachment: hubs reduce average path length (APL) exponentially, but each marginal connection yields diminishing routing gain. The betweenness term $\omega_B \cdot B_j^{\text{norm}}$ adds a secondary preference for nodes that lie on many shortest paths — "bridge" nodes that are critical for information propagation.

**Maintenance Cost $[\beta]$:** The linear cost $\beta k_i/10$ penalises over-connected agents. Without this term, agents would accumulate unlimited connections (a degenerate complete-graph equilibrium). The normalisation by 10 (the hub-tier threshold in SCOPE) ensures the cost becomes binding only when an agent's degree exceeds the hub tier.

**Social Similarity $[\gamma]$:** The Jaccard coefficient $S_{ij} = |\mathcal{N}_i \cap \mathcal{N}_j| / |\mathcal{N}_i \cup \mathcal{N}_j|$ incentivises agents with overlapping neighbourhoods to connect directly. This produces *triadic closure* — the tendency for friends-of-friends to connect — which in graph theory terms elevates the clustering coefficient $C$ and creates dense local peer cliques. High $\gamma$ produces the dense community structure observed at the periphery of SCOPE networks.

**Proof-of-Throughput $[\delta]$:** The term $\delta \cdot T_{ij}$ is a novel contribution of this work. $T_{ij} \in [0, 1]$ is the normalised historical delivery rate of peer $j$, computed as a logistic function of $j$'s degree for honest nodes, and set to $\epsilon_T = 0.001$ for detected defectors. This term embeds an *incentive-compatible* reputation mechanism: free-riders who drop packets receive near-zero throughput scores, causing rational agents to disconnect from them at the next OODA rewiring step. The mechanism is self-enforcing without requiring a centralised trusted authority.

### 4.3 Existence of Pure-Strategy Nash Equilibrium

**Theorem 4.1 (Existence via Potential Game).** *The SCOPE game $\Gamma$ admits a pure-strategy Nash Equilibrium.*

*Proof.* We show $\Gamma$ is an *exact potential game* [Monderer & Shapley, 1996] by constructing a global potential function $\Phi : E \to \mathbb{R}$ such that every individual utility gain from a rewiring action is reflected exactly in $\Phi$:

$$
\Phi(G) = \sum_{(i,j) \in E} \Big[\alpha \ln(1 + k_j) + \alpha \omega_B B_j^{\text{norm}} + \gamma S_{ij} + \delta T_{ij}\Big] - \sum_{i \in V} \frac{\beta k_i^2}{20}
\tag{2}
$$

For any unilateral edge-swap by agent $i$ (drop $(i,j^*)$, add $(i,k^*)$), one can verify that $\Delta U_i = \Delta \Phi$ exactly (detailed derivation in `docs/paper/theory_draft.md`, Lemma 4.1). Since (a) $\Phi$ is bounded above by $|E| \cdot (\alpha \ln N + \alpha \omega_B + \gamma + \delta) < \infty$, (b) each activated rewiring strictly increases $\Phi$ by at least $\epsilon_{\min} > 0$ (enforced by the 10% hysteresis threshold), and (c) the number of distinct graphs on $N$ nodes is finite ($2^{\binom{N}{2}}$), the *Best Response* dynamics cannot cycle and terminate in finite time at a state where no agent has a profitable deviation — a Pure-Strategy Nash Equilibrium. $\square$

**Remark.** The above proof invokes the *Finite Improvement Property* [Monderer & Shapley, 1996, Theorem 2.5]: any finite exact potential game where agents take turns making strict improvements must terminate at a Nash Equilibrium in finite steps.

### 4.4 Convergence Rate & OODA Loop

The OODA (Observe-Orient-Decide-Act) loop implements asynchronous best-response dynamics. At each step:

1. **Observe:** Each active agent gossips with direct neighbours to update its 2-hop memory $M_i$.
2. **Orient:** Utilities $\{U_i(j)\}_{j \in \mathcal{N}_i}$ are computed via the JIT-compiled Equation (1).
3. **Decide:** Agent identifies $(j^*, k^*) = (\arg\min U_i, \arg\max_{c \in M_i \setminus \mathcal{N}_i} U_i(c))$.
4. **Act:** If $U_i(k^*) > U_i(j^*) \cdot 1.10$, the swap is executed atomically on the shared graph.

A fraction $\rho$ of agents is activated per step (default $\rho = 0.1$), introducing controlled stochasticity. This asynchronous scheduling satisfies the conditions of Blume's [1993] stochastic fictitious play: the system converges in probability to the potential-maximising Nash Equilibrium.

### 4.5 Core-Periphery Emergence as Nash Equilibrium Topology

**Corollary 4.2 (Core-Periphery Structure at Equilibrium).** *At the Nash Equilibrium $G^*$, the graph exhibits a two-tier core-periphery topology: a dense core $C \subset V$ of high-degree hubs and a sparse periphery $V \setminus C$ of low-degree leaf nodes.*

The core forms because: (i) high-degree nodes provide large $\ln(1+k_j)$ benefit, attracting connections; (ii) logistic bandwidth $B(k_j)$ grows supralinearly for hub-tier nodes ($k_j > 10$), amplifying $\delta \cdot T_{ij}$; (iii) Jaccard similarity $S_{ij}$ among core nodes is maximal (they share many common neighbours), triggering triadic closure within the core. This self-reinforcing three-way feedback produces the observed scale-free-like degree distribution and low APL characteristic of SCOPE networks.

### 4.6 Defector Suppression as a Game-Theoretic Mechanism

**Proposition 4.3 (Free-Rider Exclusion at Equilibrium).** *In any Pure-Strategy Nash Equilibrium $G^*$, every defector node $d \in V$ has degree $k_d \to 0$.*

*Proof sketch:* A defector $d$ advertises inflated degree $k_d^{\text{adv}} = 3k_d + 5$ to attract connections, but delivers $T_{id} = 0.001$ throughput. After the first OODA observe cycle, honest agents update their throughput estimates and compute:

$$
U_i(d) = \alpha \ln(1 + k_d^{\text{adv}}) - \beta\frac{k_i}{10} + \gamma S_{id} + \delta \cdot 0.001
$$

Meanwhile, an honest hub $h$ with true degree $k_h$ provides $T_{ih} = \sigma(0.5(k_h - 10))$. For any defector with $k_d > 0$, there exists an honest alternative $h$ such that $U_i(h) > U_i(d) \cdot 1.10$, triggering a profitable deviation. At equilibrium, all agents disconnect from defectors, driving $k_d \to 0$. $\square$

---

## References (Game Theory Section)

- Monderer, D., & Shapley, L. S. (1996). Potential games. *Games and Economic Behavior*, 14(1), 124-143.
- Jackson, M. O., & Wolinsky, A. (1996). A strategic model of social and economic networks. *Journal of Economic Theory*, 71(1), 44-74.
- Blume, L. E. (1993). The statistical mechanics of strategic interaction. *Games and Economic Behavior*, 5(3), 387-424.
- Fabrikant, A., Luthra, A., Maneva, E., Papadimitriou, C. H., & Shenker, S. (2003). On a network creation game. *Proc. 22nd ACM PODC*, 347-351.
- Barabasi, A. L., & Albert, R. (1999). Emergence of scaling in random networks. *Science*, 286(5439), 509-512.
- Boyd, R., & Richerson, P. J. (1992). Punishment allows the evolution of cooperation (or anything else) in sizable groups. *Ethology and Sociobiology*, 13(3), 171-195.
