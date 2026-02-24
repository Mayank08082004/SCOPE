import math
import random
import networkx as nx
from src.config import ALPHA, BETA, GAMMA

class PeerAgent:
    def __init__(self, node_id, graph):
        self.id = node_id
        self.graph = graph
        # Belief: Limited local view (initially just neighbors)
        self.memory = set(graph.neighbors(node_id))

    def observe(self):
        """
        PERCEPTION: Update local view.
        Discover friends-of-friends (2-hop neighbors).
        """
        try:
            current_neighbors = list(self.graph.neighbors(self.id))
        except nx.NetworkXError:
            return # Handle isolated nodes gracefully

        self.memory.update(current_neighbors)

        # Discover 2-hop neighbors (simulating gossip protocol)
        new_discoveries = set()
        for n in current_neighbors:
            new_discoveries.update(self.graph.neighbors(n))

        # Keep memory size manageable (Limited cognitive capacity)
        if len(new_discoveries) > 20:
            new_discoveries = set(random.sample(list(new_discoveries), 20))

        self.memory.update(new_discoveries)
        # Remove self from potential targets
        self.memory.discard(self.id)

    def calculate_utility(self, target_id):
        """
        REASONING: The 'Brain' of the agent.
        U = Alpha * ln(1 + Degree) - Beta * Cost + Gamma * Similarity
        """
        # 1. Centrality Benefit
        target_degree = self.graph.degree(target_id)
        benefit = ALPHA * math.log(1 + target_degree)

        # 2. Connection Cost (Linear penalty)
        my_degree = self.graph.degree(self.id)
        cost = BETA * (my_degree / 10.0)

        # 3. Social Similarity (Clustering)
        my_neighbors = set(self.graph.neighbors(self.id))
        target_neighbors = set(self.graph.neighbors(target_id))

        union_size = len(my_neighbors.union(target_neighbors))
        if union_size == 0:
            similarity = 0
        else:
            intersection_size = len(my_neighbors.intersection(target_neighbors))
            similarity = intersection_size / union_size

        social_bonus = GAMMA * similarity

        return benefit - cost + social_bonus

    def act(self):
        """
        ACTION: The OODA Loop Execution.
        Decide to rewire if a better partner is found.
        """
        # 1. Identify current worst connection
        current_neighbors = list(self.graph.neighbors(self.id))
        if not current_neighbors: return

        neighbor_utilities = {n: self.calculate_utility(n) for n in current_neighbors}
        worst_neighbor = min(neighbor_utilities, key=neighbor_utilities.get)
        worst_u = neighbor_utilities[worst_neighbor]

        # 2. Identify best potential new partner from memory
        candidates = list(self.memory - set(current_neighbors))
        if not candidates: return

        # Sample a few candidates to save compute time
        sample_candidates = random.sample(candidates, min(len(candidates), 10))
        candidate_utilities = {c: self.calculate_utility(c) for c in sample_candidates}
        best_candidate = max(candidate_utilities, key=candidate_utilities.get)
        best_u = candidate_utilities[best_candidate]

        # 3. Strategic Decision (Hysteresis Threshold)
        # Only switch if the gain is significant (> 10%)
        if best_u > worst_u * 1.1:
            if self.graph.has_edge(self.id, worst_neighbor):
                self.graph.remove_edge(self.id, worst_neighbor)
            self.graph.add_edge(self.id, best_candidate)