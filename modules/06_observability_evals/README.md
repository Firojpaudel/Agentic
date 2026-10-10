# Module 06: Observability and Sandboxed Evals

> "Grade full trajectories, in sandboxes, reproducibly. Nothing else tells you if a change helped."

---

## 1. Objectives
- Instrument agents with OpenTelemetry standards: capture cost, latency, token count, and spans per step.
- Self-host or connect to Langfuse or Phoenix for tracing and dataset curation.
- Build reproducible Trajectory Evaluations with Inspect AI rather than simple string-match tests.

---

## 2. Key Repositories to Read Line-by-Line
- **UKGovernmentBEIS/inspect_ai** (https://github.com/UKGovernmentBEIS/inspect_ai): Evaluation framework with sandboxed tasks, scorers, and trajectory logs.
- **sierra-research/tau2-bench** (https://github.com/sierra-research/tau2-bench): Simulated user evaluation framework for policy compliance.
- **langfuse/langfuse** (https://github.com/langfuse/langfuse): Self-hostable tracing, prompt versioning, and datasets.

---

## 3. Hands-On Exercises
1. Set up a local Langfuse instance and instrument your agent with OpenTelemetry tracing.
2. Build an Inspect AI benchmark of 10 multi-turn domain tasks that execute inside an isolated Docker sandbox.
3. Grade the trajectories: Score efficiency (number of tool calls), safety, and accuracy.

---

## 4. Acceptance Criteria
- Every agent run outputs a trace with cost and step-level spans.
- You can detect regressions in tool-calling efficiency before deploying updates.
