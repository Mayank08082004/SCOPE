# SCOPE Project: Comprehensive Code & Concept Walkthrough

This document serves as a complete educational guide to the **SCOPE** project. It breaks down the theoretical concepts and explains exactly how they are implemented in the code, file by file.

---

## 🧠 Part 1: The Core Concepts

Before looking at the code, it's essential to understand the three pillars of this project:

1.  **Complex Adaptive Systems (CAS):** An approach where there is no central server dictating the rules. Instead, many individual "Agents" follow simple local rules, which combined, lead to complex, intelligent global behavior (like a flock of birds).
2.  **The OODA Loop:** Borrowed from military strategy, this represents the cognitive cycle of our agents:
    *   **Observe:** Look at the local network environment (neighbors and friends-of-friends).
    *   **Orient:** Evaluate relationships using a Utility Equation based on Game Theory.
    *   **Decide:** Determine if a current connection is "bad" and if a potential new connection is better.
    *   **Act:** Break the bad connection and form the new one.
3.  **Core-Periphery Topology:** The end goal of the simulation. A random network is inefficient for searching. By executing the OODA loop, the network organically forms a dense "Core" of highly connected nodes (Hubs) surrounded by a "Periphery" of less connected nodes (Leaves).

---

## 📂 Part 2: Code Breakdown & Variable Dictionary

The project is structured into four main files. Let's look at how the concepts are coded.

### 1. `src/config.py` (The Laws of Physics)
This file defines the constants that control how the simulation behaves.

**Simulation Settings:**
*   `NUM_NODES` *(default: 500)*: The total size of the network. Kept at 500 so the simulation runs quickly on a laptop without needing a supercomputer.
*   `INITIAL_DEGREE` *(default: 4)*: When the random graph is first created, every node will have roughly 4 connections, mimicking basic unstructured networks like early Gnutella.
*   `ITERATIONS` *(default: 50)*: How many "ticks" or turns the evolutionary loop will run.
*   `REWIRING_PROB` *(default: 0.2)*: Represents "churn/activity". In every iteration, there is a 20% chance an agent will wake up and attempt to optimize its connections.

**The Utility Function Weights (Game Theory):**
These are the most important variables. They dictate how an agent "scores" another node.
*   `ALPHA` *(default: 2.0)*: **Centrality Benefit.** How badly an agent wants to connect to a popular node. A high alpha creates "Super-Hubs".
*   `BETA` *(default: 0.6)*: **Connection Cost.** Every connection requires memory and bandwidth. Beta is the penalty for having too many connections.
*   `GAMMA` *(default: 1.0)*: **Social Similarity.** A bonus given if two nodes share many mutual friends. This creates tightly knit local "clusters" which makes the network robust against failures.

**Routing Parameters:**
*   `QUERY_TTL` *(default: 20)*: **Time-To-Live**. When searching for a file, if it takes more than 20 hops, the search is considered a failure.
*   `NUM_SEARCH_QUERIES` *(default: 500)*: During Phase 2, the system simulates 500 random file requests to test how fast the network can route traffic.

---

### 2. `src/agent.py` (The Peer Agent)
This class represents a single node/computer in the network. It houses the OODA loop logic.

*   `self.memory`: A Python `set` that stores the IDs of nodes this agent knows about. It represents the agent's limited view of the world.

**Key Methods:**
*   `observe()`: The agent looks at its neighbors and its neighbors' neighbors to discover new nodes. It updates its `self.memory`. It caps memory at 100 to simulate limited cognitive capacity.
*   `calculate_utility(target_id)`: The "Brain". It calculates the score of connecting to `target_id`.
    *   *Calculation:* `Benefit (Alpha * log(degree))` - `Cost (Beta * my_degree)` + `Bonus (Gamma * similarity)`.
*   `act()`: The Execution. 
    1. It finds its current worst neighbor by calculating utility.
    2. It picks a sample of random nodes from its memory and calculates their utility.
    3. **Hysteresis Threshold:** It only breaks a connection if the new node is at least 10% better (`worst_u * 1.1`). This prevents endless, chaotic swapping.
*   `route_query()`: Implements **Gradient Ascent**. If an agent doesn't have the file, who does it ask? It asks the neighbor with the highest degree (the most popular node), assuming that node knows more of the network.
*   `calculate_bandwidth()`: **The Incentive Mechanism.** Calculates download speed using a Logistic Curve.
    *   *Variables:* `L=100` (Max speed), `k=0.5` (Steepness of curve), `x0=10` (The threshold; degrees > 10 get fast speeds). This solves the free-rider problem.

---

### 3. `src/simulation.py` (The World Engine)
This file orchestrates the environment in which the Agents live.

**Key Functions:**
*   `initialize_graph()`: Uses NetworkX's `erdos_renyi_graph` to create a totally random mathematical network. It includes a fail-safe check (`nx.is_connected`) to ensure the graph isn't broken into isolated islands.
*   `run_simulation()`: The main loop.
    1. Creates the Agents.
    2. Enters a loop `for step in range(ITERATIONS)`.
    3. Randomly wakes up a subset of agents based on `REWIRING_PROB`.
    4. Calls `agent.observe()` and `agent.act()`.
    5. After the loop, it calculates the **Average Path Length (APL)** and **Clustering Coefficient** and saves them to a `history` dictionary for plotting.
*   `test_routing_performance()`: Runs the 500 test queries. It first tries to use the Agent's "memory" to find a shortcut to the file. If that fails, it falls back to the Gradient Ascent routing logic to traverse the graph hop-by-hop.

---

### 4. `main.py` (The Dashboard)
This is the entry point that ties everything together and makes it visible.

**Key Components:**
*   `run_simulation()` is called and returns the final mathematical graph (`G`) and the data metrics (`history`).
*   **Console Output:** Prints the comparative metrics, proving that the Strategic network (~2.4 hops) is significantly better than the Random baseline (~10.8 hops). It also prints the bandwidth metrics to prove the incentive mechanism works.
*   `plot_results()`: Uses `matplotlib` and `seaborn` to generate a 2x2 grid representing the project's success:
    1.  **Line Graph (APL):** Shows latency dropping over time.
    2.  **Line Graph (Clustering):** Shows the network becoming more "social".
    3.  **Adjacency Heatmap:** Converts the graph into a Numpy Array and sorts nodes by degree. The dense black area in the top left physically proves the existence of the "Core Hubs".
    4.  **Scatter Plot:** Maps Node Degree (X) against Download Speed (Y) to visually demonstrate the Logistic Incentive curve.

---

## 🏃 Part 3: Step-by-Step Example of a Single Iteration

To truly understand how the network evolves, let's trace a single agent during one iteration (one tick) of the simulation.

**The Setup:**
Imagine **Agent A** (Degree: 3) randomly wakes up.
Agent A is currently connected to Nodes B, C, and D.

### Step 1: OBSERVE
Agent A looks at its current neighbors (B, C, D). It then asks them who *they* are connected to (simulating a gossip protocol).
*   Node B introduces Agent A to Node E.
*   Node C introduces Agent A to Node F and G.
Agent A updates its `self.memory` with this new knowledge (Nodes E, F, and G). It now has an expanded view of the network.

### Step 2: ORIENT (The Math)
Agent A evaluates its current connections to see who is the "weakest link". It calculates the Utility ($U$) for B, C, and D.
Let's calculate the Utility for **Node B** (Degree: 2). Agent A and Node B share 0 mutual friends.
*   `Alpha` = 2.0, `Beta` = 0.6, `Gamma` = 1.0. (Agent A's degree is 3).
*   **Benefit:** $2.0 \cdot \ln(1 + 2) = 2.0 \cdot 1.09 = 2.18$
*   **Cost:** $0.6 \cdot (3 / 10.0) = 0.18$
*   **Social Bonus:** $1.0 \cdot 0 = 0$
*   **Node B's Score:** $2.18 - 0.18 + 0 =$ **2.00**

Assume after calculating all three, Node B has the lowest score (2.00). **Node B is the weakest link.**

### Step 3: DECIDE
Now, Agent A looks at the new nodes in its memory (E, F, G) to see if anyone is better than Node B.
Let's say **Node G** is a highly popular "Hub" with a Degree of **15**. Agent A and Node G share 2 mutual friends out of a combined total of 16 neighbors (Similarity = 2/16 = 0.125).

Let's calculate the Utility for **Node G**:
*   **Benefit:** $2.0 \cdot \ln(1 + 15) = 2.0 \cdot 2.77 = 5.54$ *(Massive benefit because G is a hub!)*
*   **Cost:** $0.6 \cdot (3 / 10.0) = 0.18$ *(Cost is the same for Agent A)*
*   **Social Bonus:** $1.0 \cdot 0.125 = 0.125$
*   **Node G's Score:** $5.54 - 0.18 + 0.125 =$ **5.485**

**The Hysteresis Check:** 
Agent A compares its best potential option (Node G = 5.48) against its current worst option (Node B = 2.00).
Is `5.485 > (2.00 * 1.1)` ? Yes, 5.485 is vastly greater than 2.2.

### Step 4: ACT
Because the utility gain is massive, Agent A executes the rewire:
1.  It breaks the connection with Node B (`self.graph.remove_edge(A, B)`).
2.  It forms a new connection with Node G (`self.graph.add_edge(A, G)`).

**The Result:** Agent A has successfully dropped a low-value connection and connected to a powerful Hub, moving the entire network one step closer to the highly efficient "Core-Periphery" structure!

---

## 🔍 Part 4: Runthrough of a File Search (Gradient Ascent)

Once the network has evolved, Phase 2 tests its efficiency. Let's trace how a search query travels using **Gradient Ascent** routing.

**The Setup:**
*   **Target:** We are looking for a file located on **Node T**.
*   **Source:** The search begins at a random leaf node, **Node S** (Degree: 2).
*   Node S is connected to Node X (Degree: 5) and Node Y (Degree: 8).

### Step 1: Memory Check (The Shortcut)
Node S first checks its internal `self.memory`. Does it already know where Node T is from past gossip?
*   *If Yes:* It routes the query directly toward the known path. This is a massive time saver.
*   *If No:* It must forward the query blindly. Let's assume it doesn't know Node T.

### Step 2: Gradient Ascent (The Climb)
Since Node S doesn't have the file, it must ask a neighbor. The logic is: *"Ask the most popular person you know, they probably know more people."*
*   Node S compares its valid neighbors: Node X (Degree 5) and Node Y (Degree 8).
*   Because $8 > 5$, Node S forwards the query to **Node Y**. This counts as **Hop 1**.

### Step 3: Reaching the Core
Now Node Y has the query. Node Y checks its memory. It doesn't have it either.
*   Node Y's neighbors are Node S (already visited) and **Node Z**, which is a massive Core Hub with a Degree of **60**.
*   Node Y forwards the query to Node Z. This is **Hop 2**.

### Step 4: The Hub Knows All
The query is now at the center of the network (Node Z).
*   Because Node Z has 60 connections, its `self.memory` is vast.
*   Node Z checks its memory and realizes **Node T** is one of its neighbors.
*   It immediately forwards the query to Node T. This is **Hop 3**.

**The Result:** The search succeeds in just **3 hops**. In a purely random network, traversing from S to T might have involved wandering aimlessly through 10-15 nodes until the TTL (Time-To-Live) expired. The Core-Periphery structure acts as a high-speed highway system.

---

## 💰 Part 5: Runthrough of the Incentive Mechanism

Why would a node *want* to be a Hub like Node Z? Being a Hub means carrying lots of traffic, which is expensive. We solve this "Free-Rider" problem with the Logistic Bandwidth formula.

**The Formula:** 
$$Bandwidth = \frac{100}{1 + e^{-0.5 \cdot (Degree - 10)}}$$

Let's calculate the real-world download speed for the nodes in our search example:

### Case 1: The Leaf Node (Node S)
Node S only contributes 2 connections to the network (Degree = 2). It's a free-rider.
*   Math: $100 / (1 + e^{-0.5 \cdot (2 - 10)})$
*   Math: $100 / (1 + e^{4})$
*   Math: $100 / (1 + 54.59)$
*   **Result:** Node S gets a sluggish download speed of **~1.79 Mbps**.

### Case 2: The Core Hub (Node Z)
Node Z provides massive value to the network by maintaining 60 connections (Degree = 60).
*   Math: $100 / (1 + e^{-0.5 \cdot (60 - 10)})$
*   Math: $100 / (1 + e^{-25})$
*   Math: $100 / (1 + \text{nearly zero})$
*   **Result:** Node Z receives the maximum possible bandwidth: **100 Mbps**.

**The Result:** Node Z is rewarded for its hard work with speeds over 50x faster than Node S. If Node S wants faster downloads, its OODA loop must work harder to find better connections and increase its degree, driving the whole network to become healthier.

---

## 🌎 Part 6: Real-World Implementation (Overlay vs. Underlay)

When transitioning from this math-based simulation to a real-world Phase 3 prototype, a common question is: *"Where does this actually run? Does it need to be installed on Wi-Fi routers?"*

The answer is **No**. SCOPE is an **Overlay Network**. It runs entirely as software applications on standard devices (laptops, mobile phones), not on hardware routers.

Here is how the theory translates into reality:

### 1. The Underlay Network (The Physical Reality)
This is the physical internet (Layer 3 of the OSI Model). 
*   **The Hardware:** ISP routers, fiber optic cables, your home Wi-Fi.
*   **The Job:** Moving a packet of data from IP Address `A` to IP Address `B` as fast as possible across physical distances.

### 2. The SCOPE Overlay Network (The Virtual Map)
SCOPE sits *on top* of the physical internet (Layer 7 / Application Layer).
*   **The Hardware:** Standard user devices (laptops, mobile phones) running the SCOPE app in the background.
*   **The Nodes:** Every user running the app is a "Node" in our graph.
*   **The Connections (Edges):** A connection is not a physical wire. It is simply an open **TCP/UDP Socket** or **WebRTC connection** between two apps.

### How it operates in practice:
Imagine **User Peter** in New York and **User Mary** in London.
1.  **Physical Distance:** They are 3,000 miles apart. It takes 15 physical hardware ISP routers to pass a message between them.
2.  **SCOPE Topology:** During the "Act" phase of the OODA loop, Peter's app calculates that Mary's app is an excellent "Hub". So, Peter's app executes `socket.connect(Mary's IP)`. 
3.  **The Magic:** As far as your SCOPE topology is concerned, Peter and Mary are **1 hop away** (direct neighbors). Your gradient ascent search will treat them as right next to each other, even though the physical underlay relies on 15 hardware routers under the hood.

This means you do not need to configure physical networking gear to build this. You will simply build a Python, Node.js, or React Native application that opens sockets based on the utility function scores!
