# SCOPE Live Demo Pointers & Script

This document is designed to be your quick-reference sheet during the live presentation. It covers exactly **what to do** (on screen) and **what to say** (in short).

---

## 1. Introduction & The Goal (The Hook)
**What to show:**
- Slide or title screen of the project.

**What to say (in short):**
- *"Current P2P networks either need central trackers or wander blindly."*
- *"SCOPE fixes this by treating the network as a **Complex Adaptive System**."*
- *"We used Game Theory. Nodes act selfishly to find the best connections, organically creating a highly efficient 'Core-Periphery' network with zero central coordination."*

---

## 2. The Math & Phase 2 Demo (Array Simulation)
**What to show:**
- Have the Phase 2 backend running (`python app.py`).
- Open React UI to the **Simulation Dashboard**.
- Show the Adjacency Matrix and Average Path Length (APL) graphs updating.

**What to say (in short):**
- *"Here is the math simulation. Every node runs an 'OODA loop' evaluating connections based on Benefit, Cost, and Mutual Friends (Alpha, Beta, Gamma)."*
- *"Notice the Adjacency Matrix forming a dense 'Core' in the corner."*
- *"Our Average Path Length (APL) drops from ~5 hops down to ~2.6 hops."*
- *"We also added a Logistic Incentive: nodes that contribute more connections get faster download speeds, stopping 'Free-Riders'."*

---

## 3. Phase 3 Physical Swarm (The Big Reveal)
**What to show:**
- Terminal: run `docker compose up -d` to show the containers spinning up.
- React UI: switch to the **Network Dashboard** showing the live `d3-force` node graph.

**What to say (in short):**
- *"Math is great, but we wanted to prove it in reality. What you're seeing now is a **Physical Swarm of 75 isolated Docker containers**."*
- *"Each container is a node running on actual Localhost TCP sockets."*
- *"The UI is pulling live telemetry as these containers self-organize their connections in real-time."*

---

## 4. Live Routing & File Transfer
**What to show:**
- Click a Source node, then a Target node. 
- Click **"Execute Transfer"**.
- Point to the route trace on screen.

**What to say (in short):**
- *"Let's simulate a P2P file transfer."*
- *"The packet routes using 'Memory-Assisted Gradient Ascent'—meaning it hops to the most connected neighbor without getting trapped in a dead-end loop."*
- *"Notice it traversed the physical sockets in just a few hops."*

---

## 5. The Adversarial Attack (Black Hole)
**What to show:**
- Highlight a red **Defector node** on the graph.
- Try sending a file transfer through or near it, watch it drop/fail.

**What to say (in short):**
- *"We also tested security by injecting Defectors (the red nodes)."*
- *"They launch a Sybil attack by lying to the math equation, claiming they have massive network degrees."*
- *"Honest nodes flock to them, creating massive 'Black Holes' that silently drop intercepted transfers."*
- *"This proves that pure greedy routing is highly vulnerable to manipulation."*

---

## 6. Conclusion
**What to show:**
- Final slide or leave the active physical graph running on the screen.

**What to say (in short):**
- *"In conclusion, SCOPE successfully bridges Game Theory mathematical routing with physical asynchronous TCP engineering."*
- *"This lays the groundwork for fully autonomous, self-optimizing networks in IoT and Edge computing."*
