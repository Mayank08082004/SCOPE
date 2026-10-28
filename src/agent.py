import math
import random
import networkx as nx
from numba import jit
from src.config import ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT, DELTA_WEIGHT, HYSTERESIS_EPSILON

@jit(nopython=True)
def _jit_calculate_utility(
    target_degree, target_betweenness, my_degree,
    union_size, intersection_size,
    alpha, beta, gamma, bw_weight,
    delta=0.0, throughput=0.0
):
    """
    U = α·(ln(1+degree) + bw·betweenness) - β·cost + γ·similarity + δ·throughput

    The new δ·throughput term (Phase 4 — Proof-of-Throughput) rewards agents
    that connect to high-bandwidth contributors, penalising free-riders in the Nash
    equilibrium by making their utility strictly lower than contributors.
    """
    # Centrality benefit: α·[ln(1 + target_degree) + ω_B · target_betweenness]
    benefit    = alpha * (math.log(1.0 + target_degree) + bw_weight * target_betweenness)
    cost       = beta * (my_degree / 10.0)
    similarity = intersection_size / union_size if union_size > 0 else 0.0
    throughput_reward = delta * throughput
    return benefit - cost + gamma * similarity + throughput_reward


class PeerAgent:
    def __init__(self, node_id, graph, is_defector=False):
        self.id    = node_id
        self.graph = graph
        self.is_defector = is_defector
        # Belief: limited local view — initially just direct neighbours
        self.memory = set(graph.neighbors(node_id))

    # ------------------------------------------------------------------
    # PERCEPTION
    # ------------------------------------------------------------------
    def observe(self):
        """Update local view by discovering 2-hop neighbours (gossip)."""
        try:
            current_neighbors = list(self.graph.neighbors(self.id))
        except nx.NetworkXError:
            return

        self.memory.update(current_neighbors)

        new_discoveries = set()
        for n in current_neighbors:
            new_discoveries.update(self.graph.neighbors(n))

        # Cap memory size (limited cognitive capacity)
        if len(new_discoveries) > 100:
            new_discoveries = set(random.sample(list(new_discoveries), 100))

        self.memory.update(new_discoveries)
        self.memory.discard(self.id)

    # ------------------------------------------------------------------
    # REASONING
    # ------------------------------------------------------------------
    def get_advertised_degree(self, target_id):
        """Returns actual degree for honest nodes, and a highly inflated degree for defectors."""
        if not self.graph.has_node(target_id):
            return 0
        actual_degree = self.graph.degree(target_id)
        if self.graph.nodes[target_id].get('is_defector', False):
            return actual_degree * 3 + 5
        return actual_degree

    def calculate_utility(self, target_id, alpha=ALPHA, beta=BETA, gamma=GAMMA,
                          bw_weight=BETWEENNESS_WEIGHT, delta=DELTA_WEIGHT):
        """
        U = α·(ln(1+Degree) + bw·Betweenness) - β·Cost + γ·Similarity + δ·Throughput

        The δ·Throughput term (Proof-of-Throughput) rewards this agent's own
        upload contribution, making the Nash equilibrium strictly prefer
        contributor nodes over free-riders.
        """
        # Clean memory if target is dead
        if not self.graph.has_node(target_id):
            self.memory.discard(target_id)
            return -999.0

        # 1. Centrality benefit (target's properties)
        target_degree = self.get_advertised_degree(target_id)
        betweenness   = self.graph.nodes[target_id].get('betweenness', 0.0)

        # 2. Connection cost (self's degree)
        my_degree = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0

        # 3. Social similarity (Jaccard overlap of neighbour sets)
        my_neighbors     = set(self.graph.neighbors(self.id)) if self.graph.has_node(self.id) else set()
        target_neighbors = set(self.graph.neighbors(target_id))
        union_size        = len(my_neighbors | target_neighbors)
        intersection_size = len(my_neighbors & target_neighbors)

        # 4. Proof-of-Throughput reward (target's throughput contribution)
        #    Normalised to [0, 1] range: max bandwidth L=100 Mbps → divide by 100.
        #    Defectors contribute minimal bandwidth (~0.1 Mbps); honest nodes scale via logistic curve.
        is_target_defector = self.graph.nodes[target_id].get('is_defector', False)
        if is_target_defector:
            target_throughput = 0.001
        else:
            target_throughput = 1.0 / (1.0 + math.exp(-0.5 * (target_degree - 10.0)))

        return _jit_calculate_utility(
            float(target_degree), float(betweenness), float(my_degree),
            float(union_size), float(intersection_size),
            float(alpha), float(beta), float(gamma), float(bw_weight),
            float(delta), float(target_throughput)
        )

    # ------------------------------------------------------------------
    # ACTION  (OODA loop execution)
    # ------------------------------------------------------------------
    def act(self, alpha=ALPHA, beta=BETA, gamma=GAMMA, bw_weight=BETWEENNESS_WEIGHT, delta=DELTA_WEIGHT):
        """Rewire: drop worst connection, add best candidate from memory."""
        if not self.graph.has_node(self.id):
            return

        current_neighbors = list(self.graph.neighbors(self.id))
        if not current_neighbors:
            return

        # Identify current worst connection
        neighbor_utilities = {n: self.calculate_utility(n, alpha, beta, gamma, bw_weight, delta) for n in current_neighbors}
        worst_neighbor = min(neighbor_utilities, key=neighbor_utilities.get)
        worst_u        = neighbor_utilities[worst_neighbor]

        # Identify best potential new partner from memory
        candidates = list(self.memory - set(current_neighbors))
        if not candidates:
            return

        sample_candidates   = random.sample(candidates, min(len(candidates), 10))
        candidate_utilities = {c: self.calculate_utility(c, alpha, beta, gamma, bw_weight, delta) for c in sample_candidates}
        best_candidate = max(candidate_utilities, key=candidate_utilities.get)
        best_u         = candidate_utilities[best_candidate]

        # Robust hysteresis threshold: ΔU > ε · max(0.01, |U_worst|)
        if (best_u - worst_u) > HYSTERESIS_EPSILON * max(0.01, abs(worst_u)):
            if self.graph.has_edge(self.id, worst_neighbor):
                self.graph.remove_edge(self.id, worst_neighbor)
            self.graph.add_edge(self.id, best_candidate)

    def decide(self, alpha=ALPHA, beta=BETA, gamma=GAMMA, bw_weight=BETWEENNESS_WEIGHT, delta=DELTA_WEIGHT):
        """
        Sequential OODA step: observe, evaluate utility (including δ·throughput),
        and return the rewiring decision without mutating the graph.

        Returns: (agent_id, edge_to_drop, edge_to_add, new_memory)
        """
        self.observe()

        if not self.graph.has_node(self.id):
            return (self.id, None, None, self.memory)

        current_neighbors = list(self.graph.neighbors(self.id))
        if not current_neighbors:
            return (self.id, None, None, self.memory)

        neighbor_utilities = {
            n: self.calculate_utility(n, alpha, beta, gamma, bw_weight, delta)
            for n in current_neighbors
        }
        worst_neighbor = min(neighbor_utilities, key=neighbor_utilities.get)
        worst_u        = neighbor_utilities[worst_neighbor]

        candidates = list(self.memory - set(current_neighbors))
        if not candidates:
            return (self.id, None, None, self.memory)

        sample_candidates   = random.sample(candidates, min(len(candidates), 10))
        candidate_utilities = {
            c: self.calculate_utility(c, alpha, beta, gamma, bw_weight, delta)
            for c in sample_candidates
        }
        best_candidate = max(candidate_utilities, key=candidate_utilities.get)
        best_u         = candidate_utilities[best_candidate]

        # Robust hysteresis threshold: ΔU > ε · max(0.01, |U_worst|)
        if (best_u - worst_u) > HYSTERESIS_EPSILON * max(0.01, abs(worst_u)):
            return (self.id, worst_neighbor, best_candidate, self.memory)

        return (self.id, None, None, self.memory)

    # ------------------------------------------------------------------
    # INCENTIVE MECHANISM
    # ------------------------------------------------------------------
    def calculate_bandwidth(self):
        """
        Logistic bandwidth:  f(x) = L / (1 + exp(-k(x - x0)))
        Higher-degree hubs are rewarded with faster download speeds.
        """
        degree = self.graph.degree(self.id)
        if self.is_defector:
            return 0.0 # Free-riders contribute no bandwidth
        L  = 100   # max bandwidth (Mbps)
        k  = 0.5   # steepness
        x0 = 10    # midpoint (degree > 10 → hub tier)
        return L / (1 + math.exp(-k * (degree - x0)))

    # ------------------------------------------------------------------
    # ROUTING  (gradient ascent)
    # ------------------------------------------------------------------
    def route_query(self, target_id, visited, ttl):
        """
        Forward to the unvisited neighbour with the highest degree.
        Returns (found: bool, next_hop_or_visited).
        """
        if self.id == target_id:
            return True, visited

        if self.is_defector:
            # Free-riders drop the packet instead of forwarding
            return False, visited

        if ttl <= 0:
            return False, visited

        visited.append(self.id)

        try:
            neighbors = list(self.graph.neighbors(self.id))
        except Exception:
            return False, visited

        valid = [n for n in neighbors if n not in visited]
        if not valid:
            return False, visited

        best = max(valid, key=lambda n: self.graph.degree(n))
        return False, best


# ======================================================================
# ADVERSARIAL AGENT SUBCLASSES  (Task 2.1 — Member 2: Samarth Dave)
# ======================================================================
# Each class models a distinct adversarial strategy for the multi-type
# defector evaluation required by Reviewer Issue D.


class NaiveLiarAgent(PeerAgent):
    """
    Type 1 — Naive Liar
    Inflates advertised degree to 3k+5 and drops 100% of forwarded packets.
    Throughput contribution is minimal (T = 0.001).
    This is the easiest attacker to detect via throughput verification.
    """
    DEFECTOR_TYPE = 'naive_liar'

    def __init__(self, node_id, graph, **kwargs):
        super().__init__(node_id, graph, is_defector=True)

    def get_advertised_degree(self, target_id):
        """Inflates the degree of the target if this agent is the one advertising."""
        if target_id == self.id:
            actual = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0
            return actual * 3 + 5
        # For other targets, return their actual degree
        if not self.graph.has_node(target_id):
            return 0
        return self.graph.degree(target_id)

    def route_query(self, target_id, visited, ttl):
        """Drops all forwarded packets (black hole attack)."""
        return False, visited

    def calculate_bandwidth(self):
        """Free-riders contribute minimal bandwidth."""
        return 0.1  # near-zero contribution


class IntermittentDropperAgent(PeerAgent):
    """
    Type 2 — Intermittent Dropper
    Reports truthful degree but probabilistically drops 50% of forwarded traffic.
    Harder to detect than Type 1 because advertised metrics are honest.
    """
    DEFECTOR_TYPE = 'intermittent_dropper'
    DROP_PROBABILITY = 0.50

    def __init__(self, node_id, graph, **kwargs):
        super().__init__(node_id, graph, is_defector=True)

    def get_advertised_degree(self, target_id):
        """Reports truthful degree — no inflation."""
        if not self.graph.has_node(target_id):
            return 0
        return self.graph.degree(target_id)

    def route_query(self, target_id, visited, ttl):
        """Drops packets with 50% probability."""
        if random.random() < self.DROP_PROBABILITY:
            return False, visited  # silently drop
        # Otherwise, forward honestly
        return super().route_query(target_id, visited, ttl)

    def calculate_bandwidth(self):
        """Contributes roughly half bandwidth due to drops."""
        degree = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0
        L, k, x0 = 100, 0.5, 10
        full_bw = L / (1 + math.exp(-k * (degree - x0)))
        return full_bw * (1.0 - self.DROP_PROBABILITY)


class ColludingSybilAgent(PeerAgent):
    """
    Type 3 — Colluding Sybil Cluster
    Members of a sybil clique falsely exchange maximum throughput ratings
    with each other and inflate each other's advertised degree.
    Sybil cluster membership is tracked via a shared class-level set.
    """
    DEFECTOR_TYPE = 'colluding_sybil'
    _sybil_clique = set()  # class-level: shared across all sybil instances

    def __init__(self, node_id, graph, **kwargs):
        super().__init__(node_id, graph, is_defector=True)
        ColludingSybilAgent._sybil_clique.add(node_id)

    @classmethod
    def reset_clique(cls):
        """Reset the sybil clique membership (call before each experiment)."""
        cls._sybil_clique = set()

    def get_advertised_degree(self, target_id):
        """Inflate degree for fellow sybil nodes, truthful for others."""
        if not self.graph.has_node(target_id):
            return 0
        actual = self.graph.degree(target_id)
        if target_id in self._sybil_clique:
            return actual * 3 + 5  # boost clique members
        return actual

    def calculate_utility(self, target_id, alpha=ALPHA, beta=BETA, gamma=GAMMA,
                          bw_weight=BETWEENNESS_WEIGHT, delta=DELTA_WEIGHT):
        """Override to give maximum throughput score to fellow sybil nodes."""
        if target_id in self._sybil_clique:
            # Fabricate extremely high throughput for clique members
            if not self.graph.has_node(target_id):
                self.memory.discard(target_id)
                return -999.0
            target_degree = self.get_advertised_degree(target_id)
            betweenness = self.graph.nodes[target_id].get('betweenness', 0.0)
            my_degree = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0
            my_neighbors = set(self.graph.neighbors(self.id)) if self.graph.has_node(self.id) else set()
            target_neighbors = set(self.graph.neighbors(target_id))
            union_size = len(my_neighbors | target_neighbors)
            intersection_size = len(my_neighbors & target_neighbors)
            return _jit_calculate_utility(
                float(target_degree), float(betweenness), float(my_degree),
                float(union_size), float(intersection_size),
                float(alpha), float(beta), float(gamma), float(bw_weight),
                float(delta), 1.0  # fabricated max throughput for clique members
            )
        return super().calculate_utility(target_id, alpha, beta, gamma, bw_weight, delta)

    def route_query(self, target_id, visited, ttl):
        """Drops packets from non-sybil sources."""
        if random.random() < 0.7:  # drops 70% of non-clique traffic
            return False, visited
        return super().route_query(target_id, visited, ttl)

    def calculate_bandwidth(self):
        """Minimal actual bandwidth contribution."""
        return 0.5


class SleeperAgent(PeerAgent):
    """
    Type 4 — Sleeper Agent
    Behaves honestly for the first `activation_steps` OODA iterations.
    After acquiring degree >= `activation_degree`, switches to defector mode:
    starts inflating degree and dropping packets.
    This is the hardest attacker to detect because historical behavior is clean.
    """
    DEFECTOR_TYPE = 'sleeper'

    def __init__(self, node_id, graph, activation_steps=10, activation_degree=10, **kwargs):
        super().__init__(node_id, graph, is_defector=False)  # starts honest
        self._activation_steps = activation_steps
        self._activation_degree = activation_degree
        self._steps_taken = 0
        self._activated = False
        self._is_sleeper = True  # internal flag for tracking

    @property
    def is_actually_malicious(self):
        """True — this node is ultimately adversarial regardless of current state."""
        return True

    def _check_activation(self):
        """Check if activation conditions are met."""
        self._steps_taken += 1
        if not self._activated:
            current_degree = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0
            if self._steps_taken >= self._activation_steps and current_degree >= self._activation_degree:
                self._activated = True
                self.is_defector = True

    def observe(self):
        """Observe and check activation."""
        super().observe()
        self._check_activation()

    def get_advertised_degree(self, target_id):
        """After activation, inflates own degree."""
        if self._activated and target_id == self.id:
            actual = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0
            return actual * 3 + 5
        if not self.graph.has_node(target_id):
            return 0
        return self.graph.degree(target_id)

    def route_query(self, target_id, visited, ttl):
        """After activation, drops all packets."""
        if self._activated:
            return False, visited
        return super().route_query(target_id, visited, ttl)

    def calculate_bandwidth(self):
        """After activation, contributes near-zero bandwidth."""
        if self._activated:
            return 0.1
        return super().calculate_bandwidth()


# ======================================================================
# ADVERSARIAL AGENT FACTORY
# ======================================================================
ADVERSARY_TYPES = {
    'naive_liar':           NaiveLiarAgent,
    'intermittent_dropper': IntermittentDropperAgent,
    'colluding_sybil':      ColludingSybilAgent,
    'sleeper':              SleeperAgent,
}


def create_adversarial_agent(agent_type, node_id, graph, **kwargs):
    """Factory function to create an adversarial agent by type name."""
    cls = ADVERSARY_TYPES.get(agent_type)
    if cls is None:
        raise ValueError(f"Unknown adversary type: {agent_type}. "
                         f"Available: {list(ADVERSARY_TYPES.keys())}")
    return cls(node_id, graph, **kwargs)
