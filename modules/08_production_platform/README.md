# Module 08: Production Agent Platform Capstone

> "Reading repos does not make you good at this. Shipping one system, measuring it, and running it reliably does."

---

## 1. Objectives
- Consolidate all previous modules into a single, production-grade agent service.
- Expose the agent via an async API (FastAPI / SSE streaming) with session management.
- Combine:
  - Protocol-standard tools (MCP)
  - Stateful orchestration (typed state machine)
  - Context compaction and tiered memory
  - Fault tolerance and gateway fallbacks (LiteLLM)
  - OpenTelemetry tracing and sandboxed evals

---

## 2. Key References
- **All-Hands-AI/OpenHands** (https://github.com/All-Hands-AI/OpenHands): Reference for production runtime architecture.
- **UKGovernmentBEIS/inspect_ai** (https://github.com/UKGovernmentBEIS/inspect_ai): CI regression testing harness.
- **pipecat-ai/pipecat** (https://github.com/pipecat-ai/pipecat): Frame-based streaming pipelines for real-time output.

---

## 3. Capstone Deliverables
1. A deployable service with Docker compose configuration.
2. An interactive evaluation suite that runs prior to any deployment.
3. Clean documentation and architecture diagrams.
