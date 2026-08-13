import math
import random
import networkx as nx
from src.config import ALPHA, BETA, GAMMA, BETWEENNESS_WEIGHT


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

    def calculate_utility(self, target_id, alpha=ALPHA, beta=BETA, gamma=GAMMA, bw_weight=BETWEENNESS_WEIGHT):
        """
        U = Alpha * (ln(1 + Degree) + BW * Betweenness) - Beta * Cost + Gamma * Similarity
        """
        # Clean memory if target is dead
        if not self.graph.has_node(target_id):
            self.memory.discard(target_id)
            return -999.0

        # 1. Centrality benefit
        target_degree = self.get_advertised_degree(target_id)
        betweenness = self.graph.nodes[target_id].get('betweenness', 0.0)
        benefit = alpha * (math.log(1 + target_degree) + bw_weight * betweenness * 100)

        # 2. Connection cost (linear penalty on own degree)
        my_degree = self.graph.degree(self.id) if self.graph.has_node(self.id) else 0
        cost = beta * (my_degree / 10.0)

        # 3. Social similarity (Jaccard index on neighbourhoods)
        my_neighbors     = set(self.graph.neighbors(self.id)) if self.graph.has_node(self.id) else set()
        target_neighbors = set(self.graph.neighbors(target_id))
        union_size = len(my_neighbors | target_neighbors)
        if union_size == 0:
            similarity = 0.0
        else:
            similarity = len(my_neighbors & target_neighbors) / union_size
        social_bonus = gamma * similarity

        return benefit - cost + social_bonus

    # ------------------------------------------------------------------
    # ACTION  (OODA loop execution)
    # ------------------------------------------------------------------
    def act(self, alpha=ALPHA, beta=BETA, gamma=GAMMA, bw_weight=BETWEENNESS_WEIGHT):
        """Rewire: drop worst connection, add best candidate from memory."""
        if not self.graph.has_node(self.id):
            return

        current_neighbors = list(self.graph.neighbors(self.id))
        if not current_neighbors:
            return

        # Identify current worst connection
        neighbor_utilities = {n: self.calculate_utility(n, alpha, beta, gamma, bw_weight) for n in current_neighbors}
        worst_neighbor = min(neighbor_utilities, key=neighbor_utilities.get)
        worst_u        = neighbor_utilities[worst_neighbor]

        # Identify best potential new partner from memory
        candidates = list(self.memory - set(current_neighbors))
        if not candidates:
            return

        sample_candidates  = random.sample(candidates, min(len(candidates), 10))
        candidate_utilities = {c: self.calculate_utility(c, alpha, beta, gamma, bw_weight) for c in sample_candidates}
        best_candidate = max(candidate_utilities, key=candidate_utilities.get)
        best_u         = candidate_utilities[best_candidate]

        # Hysteresis threshold — only switch if gain is > 10 %
        if best_u > worst_u * 1.1:
            if self.graph.has_edge(self.id, worst_neighbor):
                self.graph.remove_edge(self.id, worst_neighbor)
            self.graph.add_edge(self.id, best_candidate)

    def decide(self, alpha=ALPHA, beta=BETA, gamma=GAMMA, bw_weight=BETWEENNESS_WEIGHT):
        """
        Pure function for multiprocessing: observe and act without mutating the graph.
        Returns: (agent_id, edge_to_drop, edge_to_add, new_memory)
        """
        self.observe()
        
        if not self.graph.has_node(self.id):
            return (self.id, None, None, self.memory)

        current_neighbors = list(self.graph.neighbors(self.id))
        if not current_neighbors:
            return (self.id, None, None, self.memory)

        neighbor_utilities = {n: self.calculate_utility(n, alpha, beta, gamma, bw_weight) for n in current_neighbors}
        worst_neighbor = min(neighbor_utilities, key=neighbor_utilities.get)
        worst_u        = neighbor_utilities[worst_neighbor]

        candidates = list(self.memory - set(current_neighbors))
        if not candidates:
            return (self.id, None, None, self.memory)

        sample_candidates  = random.sample(candidates, min(len(candidates), 10))
        candidate_utilities = {c: self.calculate_utility(c, alpha, beta, gamma, bw_weight) for c in sample_candidates}
        best_candidate = max(candidate_utilities, key=candidate_utilities.get)
        best_u         = candidate_utilities[best_candidate]

        if best_u > worst_u * 1.1:
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
