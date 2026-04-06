# ==========================================
# SCOPE — CONFIGURATION PARAMETERS
# ==========================================

# Simulation Settings
NUM_NODES      = 500    # Number of agents (scaled down for speed)
INITIAL_DEGREE = 4      # Average neighbors per node (Gnutella baseline)
ITERATIONS     = 50     # How many "OODA Loops" to run
REWIRING_PROB  = 0.2    # Fraction of agents that wake up per step

# Utility Function Weights (Agent "Brain")
ALPHA = 2.0   # Weight for Centrality Benefit (desire for hubs)
BETA  = 0.6   # Weight for Connection Cost   (penalty for complexity)
GAMMA = 1.0   # Weight for Social Similarity  (clustering incentive)

# Reproducibility
SEED = 42

# Phase 2 — Search / Routing
QUERY_TTL          = 20   # Max hops before a search query fails
NUM_SEARCH_QUERIES = 500  # Number of test searches to run per evaluation
