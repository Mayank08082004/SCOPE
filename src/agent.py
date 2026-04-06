import math
import random
import networkx as nx
from src.config import ALPHA, BETA, GAMMA


class PeerAgent:
    def __init__(self, node_id, graph):
        self.id    = node_id
        self.graph = graph
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
    def calculate_utility(self, target_id):
        """
        U = Alpha * ln(1 + Degree)  -  Beta * Cost  +  Gamma * Similarity
        """
        # 1. Centrality benefit
        target_degree = self.graph.degree(target_id)
        benefit = ALPHA * math.log(1 + target_degree)

        # 2. Connection cost (linear penalty on own degree)
        my_degree = self.graph.degree(self.id)
        cost = BETA * (my_degree / 10.0)

        # 3. Social similarity (Jaccard index on neighbourhoods)
        my_neighbors     = set(self.graph.neighbors(self.id))
        target_neighbors = set(self.graph.neighbors(target_id))
        union_size = len(my_neighbors | target_neighbors)
        if union_size == 0:
            similarity = 0.0
        else:
            similarity = len(my_neighbors & target_neighbors) / union_size
        social_bonus = GAMMA * similarity

        return benefit - cost + social_bonus

    # ------------------------------------------------------------------
    # ACTION  (OODA loop execution)
    # ------------------------------------------------------------------
    def act(self):
        """Rewire: drop worst connection, add best candidate from memory."""
        current_neighbors = list(self.graph.neighbors(self.id))
        if not current_neighbors:
            return

        # Identify current worst connection
        neighbor_utilities = {n: self.calculate_utility(n) for n in current_neighbors}
        worst_neighbor = min(neighbor_utilities, key=neighbor_utilities.get)
        worst_u        = neighbor_utilities[worst_neighbor]

        # Identify best potential new partner from memory
        candidates = list(self.memory - set(current_neighbors))
        if not candidates:
            return

        sample_candidates  = random.sample(candidates, min(len(candidates), 10))
        candidate_utilities = {c: self.calculate_utility(c) for c in sample_candidates}
        best_candidate = max(candidate_utilities, key=candidate_utilities.get)
        best_u         = candidate_utilities[best_candidate]

        # Hysteresis threshold — only switch if gain is > 10 %
        if best_u > worst_u * 1.1:
            if self.graph.has_edge(self.id, worst_neighbor):
                self.graph.remove_edge(self.id, worst_neighbor)
            self.graph.add_edge(self.id, best_candidate)

    # ------------------------------------------------------------------
    # INCENTIVE MECHANISM
    # ------------------------------------------------------------------
    def calculate_bandwidth(self):
        """
        Logistic bandwidth:  f(x) = L / (1 + exp(-k(x - x0)))
        Higher-degree hubs are rewarded with faster download speeds.
        """
        degree = self.graph.degree(self.id)
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
