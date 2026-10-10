# Module 02: Orchestration and State Graphs

> "Know one graph-based framework deeply. Skim the rest to map the design space."

---

## 1. Objectives
- Move from unconstrained loops to typed, deterministic state graphs.
- Compare Pydantic AI (type-safe agents, dependency injection) vs LangGraph (state graphs, cycles, human-in-the-loop interrupts).
- Implement explicit subagent handoffs (e.g. Triage Agent to Specialist Agent).

---

## 2. Key Repositories to Read Line-by-Line
- **pydantic/pydantic-ai** (https://github.com/pydantic/pydantic-ai): Study dependency injection and typed contracts.
- **langchain-ai/langgraph** (https://github.com/langchain-ai/langgraph): Study state transitions and checkpointing.
- **openai/openai-agents-python** (https://github.com/openai/openai-agents-python): Study minimal agent handoffs and guardrail primitives.

---

## 3. Hands-On Exercises
1. Build a type-safe multi-agent triage system with `pydantic-ai`.
2. Implement a `LangGraph` state machine with an explicit Human-in-the-Loop pause before executing high-risk operations (e.g., file deletion or API calls).
3. Benchmark the latency overhead added by the framework versus the Module 01 raw loop.

---

## 4. Acceptance Criteria
- You can explain what abstractions a state machine gives you over a raw loop, and what overhead it introduces.
- You have built a working multi-agent graph with checkpoints and state recovery.
