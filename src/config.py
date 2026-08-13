# ==========================================
# SCOPE — CONFIGURATION PARAMETERS
# ==========================================

# Simulation Settings
NUM_NODES      = 10000    # Number of agents
INITIAL_DEGREE = 4      # Average neighbors per node (Gnutella baseline)
ITERATIONS     = 50     # How many "OODA Loops" to run
REWIRING_PROB  = 0.2    # Fraction of agents that wake up per step

# Churn Settings
CHURN_RATE     = 0.10   # Fraction of nodes that go offline during a churn event
CHURN_INTERVAL = 5      # Apply churn every N iterations

# Utility Function Weights (Agent "Brain")
ALPHA              = 2.0   # Weight for Centrality Benefit (desire for hubs)
BETA               = 0.6   # Weight for Connection Cost   (penalty for complexity)
GAMMA              = 1.0   # Weight for Social Similarity  (clustering incentive)
BETWEENNESS_WEIGHT = 0.5   # Weight for Betweenness Centrality bonus

# Adversarial Settings
DEFECTOR_RATIO = 0.10      # Fraction of nodes that are defectors (free-riders who lie)

# Reproducibility
SEED = 42

# Phase 2 — Search / Routing
QUERY_TTL          = 20   # Max hops before a search query fails
NUM_SEARCH_QUERIES = 500  # Number of test searches to run per evaluation
