# Module 04: Long-Horizon Harness and Memory

> "Context is the scarce resource. These decide what to keep, where, and how to get it back."

---

## 1. Objectives
- Prevent context bloat and degradation over 50+ turns using Context Condensation.
- Implement Tiered Memory: Working Context (RAM), Episodic Memory (Vector Store), and Archival Memory (Database/Graph).
- Study the event-stream architecture of long-running coding agents.

---

## 2. Key Repositories to Read Line-by-Line
- **All-Hands-AI/OpenHands** (https://github.com/All-Hands-AI/OpenHands): Event-sourcing architecture and context condenser algorithms.
- **letta-ai/letta** (https://github.com/letta-ai/letta): Memory as an operating-system problem with self-editing memory tiers.
- **mem0ai/mem0** (https://github.com/mem0ai/mem0): Extracting, consolidating, and resolving conflicting memories across sessions.

---

## 3. Hands-On Exercises
1. Build an active Context Condenser: When conversation token count exceeds 75% of window size, prune verbose tool outputs while preserving decisions, diffs, and state.
2. Build a memory agent that extracts key user facts, resolves contradictions, and injects relevant memories dynamically on startup.

---

## 4. Acceptance Criteria
- Your agent can run a 60-turn continuous session without exceeding token boundaries or forgetting the initial goal.
