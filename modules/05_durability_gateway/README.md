# Module 05: Durability and Gateway Resilience

> "What separates a demo from a system: retries, idempotency, resumable runs, cost limits, and validation."

---

## 1. Objectives
- Build crash-proof agents using Durable Execution Engines (Temporal or Restate).
- Put a unified LLM Gateway (LiteLLM) in front of all models with fallback routing, rate-limit handling, and budget caps.
- Implement idempotency keys so failing network requests do not trigger duplicate external side effects.

---

## 2. Key Repositories to Read Line-by-Line
- **temporalio/samples-python** (https://github.com/temporalio/samples-python): Study AI agent workflows with durable timers and activity retries.
- **BerriAI/litellm** (https://github.com/BerriAI/litellm): Provider failover, load balancing, per-tenant budgets, and proxy fallbacks.
- **restatedev/restate** (https://github.com/restatedev/restate): Lightweight durable execution with step journaling.

---

## 3. Hands-On Exercises
1. Wrap an agent loop inside a Temporal or Restate workflow.
2. Simulate a crash (`kill -9`) mid-task during an external tool call; verify that upon worker restart, the agent recovers state and finishes without duplicate calls.
3. Configure LiteLLM proxy with a fallback chain: Free Local Ollama -> Groq Cloud -> Gemini Flash -> OpenAI.

---

## 4. Acceptance Criteria
- Killing the worker process mid-execution does not lose conversation state or repeat idempotent tool executions.
