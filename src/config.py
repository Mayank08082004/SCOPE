# ==========================================
# CONFIGURATION PARAMETERS
# ==========================================

# Simulation Settings
NUM_NODES = 500         # Number of agents (Scaled down for speed)
INITIAL_DEGREE = 4      # Average neighbors per node (Gnutella baseline)
ITERATIONS = 20         # How many "OODA Loops" to run
REWIRING_PROB = 0.1     # Probability of an agent waking up to optimize

# Utility Function Weights (The "Brain" Logic)
ALPHA = 2.0             # Weight for Centrality Benefit (Desire for Hubs)
BETA = 0.5              # Weight for Connection Cost (Penalty for complexity)
GAMMA = 1.0             # Weight for Social Similarity (Clustering)

# Random Seed for Reproducibility
SEED = 42