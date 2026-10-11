# Module 02: Orchestration & State Graphs

> *"Frameworks hide failure modes; state machines expose them. Know state transitions deeply before delegating control."*

---

## 1. Architectural Overview

Module 01 introduced the raw, unconstrained ReAct loop. While flexible, a single linear loop struggles as complexity grows:
- **No Boundary Guardrails**: Tool selection space grows unwieldy for a single model prompt.
- **Uncontrolled Mutation**: High-risk operations (database writes, financial charges, patient bookings) can be executed without supervision.
- **No Recoverable State**: If a long-running workflow crashes or awaits human input, linear while-loops cannot safely serialize and pause execution.

**Module 02 solves this through a Typed StateGraph:**
A directed graph of specialist sub-agents, deterministic intent routing, and Human-in-the-Loop (HITL) checkpoints.

```mermaid
graph TD
    Start(["&nbsp;User Request&nbsp;"]) --> Triage["&nbsp;Triage Router&nbsp;<br/>&nbsp;Node&nbsp;"]
    
    Triage -->|Intent: Appointment| AptNode["&nbsp;Appointment&nbsp;<br/>&nbsp;Specialist&nbsp;"]
    Triage -->|Intent: Ticketing| TckNode["&nbsp;Ticketing&nbsp;<br/>&nbsp;Specialist&nbsp;"]
    Triage -->|Intent: General| GenNode["&nbsp;General Help&nbsp;<br/>&nbsp;Node&nbsp;"]
    
    AptNode -->|Availability Query| EndNode(["&nbsp;Final Response&nbsp;"])
    AptNode -->|Booking Request| CheckConflict{"&nbsp;Scheduling&nbsp;<br/>&nbsp;Conflict?&nbsp;"}
    CheckConflict -->|Yes| ConflictFeedback["&nbsp;Suggest&nbsp;<br/>&nbsp;Alternative&nbsp;<br/>&nbsp;Slots&nbsp;"] --> EndNode
    CheckConflict -->|No| HITLGate1{"&nbsp;Proposal:&nbsp;<br/>&nbsp;PENDING&nbsp;"}
    
    TckNode -->|Low/Med Severity| AutoFile["&nbsp;Auto-File&nbsp;<br/>&nbsp;Support&nbsp;<br/>&nbsp;Ticket&nbsp;"] --> EndNode
    TckNode -->|High/Critical Severity| HITLGate2{"&nbsp;Proposal:&nbsp;<br/>&nbsp;PENDING&nbsp;"}
    
    HITLGate1 -->|Checkpoint Saved| HumanPause["&nbsp;⏸️ Paused for&nbsp;<br/>&nbsp;Approval&nbsp;"]
    HITLGate2 -->|Checkpoint Saved| HumanPause
    
    HumanPause -->|Resume: Approved| Executor["&nbsp;Execute&nbsp;<br/>&nbsp;Action Node&nbsp;"] --> EndNode
    HumanPause -->|Resume: Rejected| Rejection["&nbsp;Rejection&nbsp;<br/>&nbsp;Handler&nbsp;<br/>&nbsp;&amp; Feedback&nbsp;"] --> EndNode

    style HumanPause fill:#d32f2f,stroke:#b71c1c,color:#fff
    style Executor fill:#2e7d32,stroke:#1b5e20,color:#fff
    style Rejection fill:#f57c00,stroke:#e65100,color:#fff
```

---

## 2. Core Components

| Component | File | Responsibility |
| :--- | :--- | :--- |
| **Typed State Contracts** | [`src/state.py`](src/state.py) | Pydantic models: `AgentState`, `ActionProposal`, `ApprovalStatus`, `IntentType`. |
| **Domain Stores** | [`src/domain_tools.py`](src/domain_tools.py) | In-memory doctor scheduling calendars and support ticketing stores with conflict detection. |
| **StateGraph Engine** | [`src/graph.py`](src/graph.py) | First-principles directed graph engine, conditional branch routing, and checkpoint resume mechanics. |
| **Specialist Agents** | [`src/specialists.py`](src/specialists.py) | `triage_router_node`, `appointment_specialist_node`, `ticketing_specialist_node`, `action_executor_node`. |
| **Graph Assembly** | [`src/engine.py`](src/engine.py) | Compiles nodes and routing edges into an executable state machine. |
| **Latency Benchmark** | [`src/benchmark.py`](src/benchmark.py) | Microsecond-precision benchmark comparing StateGraph overhead against raw procedural loops. |

---

## 3. Human-in-the-Loop (HITL) Checkpoint Mechanics

In production agentic architectures, automated agents **must never execute high-risk or irreversible mutations** (such as updating hospital records, filing critical outages, or charging cards) without an approval gateway.

### Checkpoint Lifecycle:
1. **Proposal Generation**: The specialist creates an `ActionProposal(status=ApprovalStatus.PENDING)` and attaches it to `state.pending_action`.
2. **Execution Halt**: `CompiledGraph.run()` detects the pending proposal, snapshots the entire `AgentState` into `checkpoints[session_id]`, and returns `(state, is_interrupted=True)`.
3. **Supervisor Review**: A human reviewer inspects the proposal via UI/CLI and responds with `approved: bool` and optional `reviewer_notes`.
4. **Resumed Execution**: Calling `graph.resume(session_id, approved=True/False)` resumes execution from the saved checkpoint, dispatching either to `action_executor` or `handle_rejection`.

```python
# 1. Initiate workflow
state = AgentState()
state.add_message("user", "Book Dr. Sarah Chen on 2026-10-15 at 09:00 for patient Mark Peterson")
paused_state, is_interrupted = graph.run(state)

assert is_interrupted is True
print(paused_state.pending_action.description)
# -> "Book consultation for patient Mark Peterson with Dr. Sarah Chen on 2026-10-15 at 09:00"

# 2. Human supervisor approves
resumed_state, _ = graph.resume(
    session_id=paused_state.session_id,
    approved=True,
    reviewer_notes="Insurance verified"
)
print(resumed_state.final_output)
# -> "Booking Confirmed: APT-20261015-0900 | Patient: Mark Peterson ..."
```

---

## 4. Latency & Framework Overhead

Running `python modules/02_orchestration/src/benchmark.py` yields the following profile:

| Metric | Raw Procedural Baseline | Typed StateGraph Engine |
| :--- | :--- | :--- |
| **Average Latency per step** | ~1.5 µs | ~35 µs |
| **Transition Overhead** | Baseline | ~33.5 µs |
| **Impact on LLM Operations** | 0.00% | < 0.01% (LLM inference takes 150,000–500,000 µs) |

> **Conclusion**: The architectural guarantees of typed contracts, transition auditing, and interruptible checkpoints cost microsecond-level overhead while eliminating unconstrained failure modes.

---

## 5. Running Tests & Demos

```bash
# Run deterministic unit tests
./.venv/bin/pytest modules/02_orchestration/tests/ -v

# Run interactive Rich terminal demonstration
./.venv/bin/python modules/02_orchestration/run.py
```
