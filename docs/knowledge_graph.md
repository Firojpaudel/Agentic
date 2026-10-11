# System Knowledge Graph and Architecture Map

This document is the persistent memory and architecture map for the Agentic Systems lab. It records progress, component relationships, and milestones leading to the voice-driven appointment and ticketing agent.

---

## 1. System Knowledge Graph

```mermaid
graph TD
    subgraph UserInterface ["&nbsp;Input and Voice Layer&nbsp;"]
        VI["&nbsp;Voice Stream&nbsp;<br/>&nbsp;(Audio)&nbsp;"] --> STT["&nbsp;Speech to&nbsp;<br/>&nbsp;Text (STT)&nbsp;"]
        TI["&nbsp;Terminal CLI&nbsp;<br/>&nbsp;Input&nbsp;"] --> SharedUI["&nbsp;shared.console&nbsp;<br/>&nbsp;(UI)&nbsp;"]
        STT --> ST["&nbsp;State Input&nbsp;"]
        TI --> ST
    end

    subgraph OrchestrationLayer ["&nbsp;Module 02: State Graph&nbsp;"]
        ST --> TG["&nbsp;Triage Router&nbsp;<br/>&nbsp;Node&nbsp;"]
        TG -->|Booking Intent| BA["&nbsp;Appointment&nbsp;<br/>&nbsp;Specialist&nbsp;"]
        TG -->|Meeting Intent| MA["&nbsp;Meeting&nbsp;<br/>&nbsp;Specialist&nbsp;"]
        TG -->|Support Intent| TA["&nbsp;Ticketing&nbsp;<br/>&nbsp;Specialist&nbsp;"]
        TG -->|General Coding| CA["&nbsp;Code & Math&nbsp;<br/>&nbsp;Specialist&nbsp;"]
    end

    subgraph ToolsAndProtocols ["&nbsp;Module 01 & 03: Tools & MCP&nbsp;"]
        TR["&nbsp;Tool Registry&nbsp;"]
        BA -->|Book / Check Slots| HT["&nbsp;Hospital&nbsp;<br/>&nbsp;Booking Tool&nbsp;"]
        MA -->|Generate Links| GM["&nbsp;Calendar&nbsp;<br/>&nbsp;&amp; Meet Tool&nbsp;"]
        TA -->|Create / Update| TT["&nbsp;Ticketing&nbsp;<br/>&nbsp;Tool&nbsp;"]
        CA -->|Exec / Compute| CT["&nbsp;calculate /&nbsp;<br/>&nbsp;run_cmd&nbsp;"]
        TR -.-> HT
        TR -.-> GM
        TR -.-> TT
        TR -.-> CT
    end

    subgraph SafetyAndDurability ["&nbsp;Module 02 & 05: HITL & Resilience&nbsp;"]
        HT -->|Critical Action| HITL["&nbsp;Human Approval&nbsp;<br/>&nbsp;Checkpoint&nbsp;"]
        TT -->|Critical Action| HITL
        HITL -->|Approved| COMMIT["&nbsp;Execute API&nbsp;"]
        HITL -->|Rejected| FEEDBACK["&nbsp;Self-Correct&nbsp;<br/>&nbsp;Loop&nbsp;"]
        COMMIT --> MEM["&nbsp;Tiered&nbsp;<br/>&nbsp;Memory&nbsp;"]
    end

    subgraph OutputLayer ["&nbsp;Voice and Text Output&nbsp;"]
        MEM --> SYNTH["&nbsp;Final&nbsp;<br/>&nbsp;Synthesis&nbsp;"]
        SYNTH --> TTS["&nbsp;Text to Speech&nbsp;<br/>&nbsp;(TTS)&nbsp;"]
        SYNTH --> OUT["&nbsp;Console&nbsp;<br/>&nbsp;Markdown&nbsp;"]
    end

    style CT fill:#2e7d32,stroke:#1b5e20,color:#fff
    style TR fill:#2e7d32,stroke:#1b5e20,color:#fff
    style SharedUI fill:#2e7d32,stroke:#1b5e20,color:#fff
    style HITL fill:#d32f2f,stroke:#b71c1c,color:#fff
    style COMMIT fill:#2e7d32,stroke:#1b5e20,color:#fff
```

---

## 2. Milestone Progression to Target Application

| Stage | Subsystem | Target Capability | Status |
| :--- | :--- | :--- | :--- |
| **Stage 1** | Module 01: Raw Loop | Zero-framework ReAct loop, Safe Tool Registry, context truncation | **COMPLETED** |
| **Stage 2** | Module 02: State Graph | Triage Router, Specialist nodes, Human-in-the-Loop approval checkpoints | **COMPLETED** |
| **Stage 3** | Module 03: Protocol (MCP) | Calendar Tools, Appointment Tools, Ticket Management Tools over MCP | **NEXT** |
| **Stage 4** | Module 04: Tiered Memory | Persistent user/patient profiles, booking history, conflict resolution | Pending |
| **Stage 5** | Module 05: Durability | Crash-proof workflows so telephone/web calls do not drop state | Pending |
| **Stage 6** | Voice Streaming | Real-time speech pipeline (STT -> State Graph -> TTS audio playback) | Pending |

---

## 3. Component Inventory (Shipped So Far)

### `shared/console.py`
- Centralized terminal presentation engine with colorized traces, tool logs, observation formatting, and Markdown rendering.

### `shared/config.py`
- Unified zero-cost LLM configuration manager for Groq, Gemini Flash, OpenRouter free models, and local Ollama.

### `modules/01_raw_loop/`
- `RawAgent`: Pure Python ReAct loop with Pydantic serialization, closed-loop error feedback, and OpenAI JSON schema generation.
- `ToolRegistry`: Safe tool registration, automated schemas, parameter casting, and error sandboxing.
- `calculate`, `read_file`, `run_command`: Standard ReAct tooling suite.

### `modules/02_orchestration/`
- `state.py`: Typed contracts for `AgentState`, `ActionProposal`, `ApprovalStatus`, and domain entities.
- `graph.py`: Deterministic first-principles `StateGraph` and `CompiledGraph` engine with checkpoint resume mechanics.
- `domain_tools.py`: In-memory `HospitalScheduler` and `TicketStore` with conflict resolution and automated severity heuristics.
- `specialists.py`: `TriageRouter`, `AppointmentSpecialist`, `TicketingSpecialist`, `ActionExecutor`, and `RejectionHandler`.
- `engine.py`: Multi-agent graph assembly with conditional intent-based routing.
- `benchmark.py`: Overhead benchmarking verifying sub-20µs transition overhead.
- `run.py`: Rich terminal demonstration with interactive and automated HITL pause/approval scenarios.

---

## 4. Architectural Decisions Log

- **ADR-001: Zero-Cost Policy**: All models must use free providers (Groq free tier with `qwen/qwen3.8-27b`, Google AI Studio Gemini Flash, OpenRouter free, or local Ollama). No paid subscriptions.
- **ADR-002: Closed-Loop Error Feedback**: Tools must never raise unhandled exceptions. Errors must return as observations to allow the model to self-correct.
- **ADR-003: Contract-Driven Output**: No emojis, no conversational cheerleading. Outputs must be structured, technical Markdown.
- **ADR-004: Modular Architecture**: Each learning stage is a standalone package with dedicated test suites and README guides.
