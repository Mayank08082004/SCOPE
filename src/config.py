# ==========================================
# CONFIGURATION PARAMETERS
# ==========================================

# Simulation Settings
NUM_NODES = 500         # Number of agents (Scaled down for speed)
INITIAL_DEGREE = 4      # Average neighbors per node (Gnutella baseline)
ITERATIONS = 50         # How many "OODA Loops" to run
REWIRING_PROB = 0.2     # Probability of an agent waking up to optimize

# Utility Function Weights (The "Brain" Logic)
ALPHA = 2.0             # Weight for Centrality Benefit (Desire for Hubs)
BETA = 0.6             # Weight for Connection Cost (Penalty for complexity)
GAMMA = 1.0             # Weight for Social Similarity (Clustering)

# Random Seed for Reproducibility
SEED = 42

# --- Phase 2: Search/Routing Settings ---
QUERY_TTL = 20         # Max hops before a search fails
NUM_SEARCH_QUERIES = 500 # How many test searches to run