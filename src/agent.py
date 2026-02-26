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
        # UPGRADE: Increased memory from 20 to 100 to improve routing lookahead
        if len(new_discoveries) > 100:
            new_discoveries = set(random.sample(list(new_discoveries), 100))

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

    def route_query(self, target_id, visited, ttl):
        """
        ROUTING LOGIC (Gradient Ascent):
        1. Check if I am the target or have the file (simplified as reaching target_id).
        2. If not, forward to the neighbor with highest Degree Centrality.
        """
        # 1. Base Cases
        if self.id == target_id:
            return True, visited # Found it!
        
        if ttl <= 0:
            return False, visited # Run out of gas (TTL expired)

        # 2. Add self to visited path
        visited.append(self.id)

        # 3. Get neighbors
        try:
            neighbors = list(self.graph.neighbors(self.id))
        except:
            return False, visited

        # Filter out already visited nodes to prevent loops
        valid_neighbors = [n for n in neighbors if n not in visited]

        if not valid_neighbors:
            return False, visited # Dead end

        # 4. GRADIENT ASCENT STRATEGY
        # Pick the neighbor with the HIGHEST Degree Centrality
        # (This implies: "Ask the most popular guy, he probably knows")
        best_neighbor = max(valid_neighbors, key=lambda n: self.graph.degree(n))
        
        # In a real simulation, we would call the neighbor's agent. 
        # Here we simulate the recursive hop.
        return False, best_neighbor # Return the next hop ID