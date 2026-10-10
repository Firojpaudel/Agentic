# Agentic Systems: Zero to Production

A rigorous, modular engineering laboratory for learning, building, and shipping production-grade Agentic Systems from first principles.

Reference: Agentic Systems Atlas (Curated open-source guide)

---

## 1. Philosophy: Divide and Conquer

Frameworks (LangChain, CrewAI, AutoGen) often hide the real failure modes of agentic systems behind layers of abstraction. To engineer agents at a production level:

1. **Deconstruct the Black Box**: Write the raw while-loop, state machines, and tool execution engines by hand before reaching for frameworks.
2. **Treat Non-Determinism with Engineering Discipline**: Sandboxing, idempotency, retry budgets, typed schemas, and trajectory evals.
3. **Build and Own Every Line**: Each submodule is a standalone, self-guided lab with an architectural README. You write the code and verify the behavior.

---

## 2. Workspace Architecture

```
Agentic/
├── Agentic Systems Atlas.html         # Curated atlas of 59 repos, 11 tracks, and papers
├── pyproject.toml                     # Python dependencies
├── .env.example                       # Local and free-tier API configurations
├── README.md                          # Master roadmap and tracking
│
├── modules/
│   ├── 01_raw_loop/                   # Module 01: Raw Loop (Zero-framework ReAct)
│   ├── 02_orchestration/              # Module 02: Typed State Machines and Handoffs
│   ├── 03_protocols_mcp/              # Module 03: Model Context Protocol (FastMCP)
│   ├── 04_harness_memory/             # Module 04: Long-Horizon Context and Memory Tiers
│   ├── 05_durability_gateway/         # Module 05: Fault Tolerance, LiteLLM, and Temporal
│   ├── 06_observability_evals/        # Module 06: Tracing (Langfuse) and Evals (Inspect AI)
│   ├── 07_serving_optimization/       # Module 07: Prefix Caching and Serving (SGLang/vLLM)
│   └── 08_production_platform/        # Module 08: Production Agent Platform Capstone
```

---

## 3. Curriculum and Module Progression

| Module | Core Question | Key Open-Source References | Hands-on Build Deliverable |
| :--- | :--- | :--- | :--- |
| [01. Raw Loop](modules/01_raw_loop/) | What is the minimal code needed for autonomy? | `SWE-agent/mini-swe-agent`, `huggingface/smolagents` | Pure Python ReAct loop with 3 tools and crash recovery |
| [02. Orchestration](modules/02_orchestration/) | How do we make agents predictable and typed? | `pydantic-ai`, `langgraph` | Type-safe graph workflow with human-in-the-loop |
| [03. Protocols (MCP)](modules/03_protocols_mcp/) | How do agents talk to tools and other agents? | `modelcontextprotocol`, `fastmcp` | Custom MCP Server + client integration |
| [04. Long-Horizon Harness](modules/04_harness_memory/) | How do agents survive 50+ steps without getting lost? | `OpenHands`, `letta`, `mem0` | Context condenser and tiered memory system |
| [05. Durability and Gateway](modules/05_durability_gateway/) | What happens when models fail or workers crash? | `temporal`, `litellm` | Resumable durable workflow + fallback gateway |
| [06. Evals and Tracing](modules/06_observability_evals/) | How do you grade an agent trajectory? | `inspect_ai`, `tau2-bench`, `langfuse` | Benchmark suite with sandboxed execution |
| [07. Serving Economics](modules/07_serving_optimization/) | Why does prefix caching dominate agent speed and cost? | `sglang`, `vllm` | RadixAttention benchmark on agent history |
| [08. Production Capstone](modules/08_production_platform/) | How do all pieces fit into a shipped product? | Full stack integration | High-throughput, self-healing agent API service |

---

## 4. Zero-Cost Quickstart

You do not need paid API credits to complete this curriculum:
1. **Local**: Install Ollama with `qwen2.5-coder:7b` or `llama3.1:8b`.
2. **Free Cloud**: Use Google AI Studio (Gemini 2.0 Flash free tier) or Groq (Llama 3.3 70B free tier).
3. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Add your free API key or keep local Ollama default
   ```

---

## 5. Progress Checklist

- [x] Module 01: Raw Loop and Primitives
- [ ] Module 02: Orchestration and State Graphs
- [ ] Module 03: Protocol Layer and FastMCP
- [ ] Module 04: Context Compaction and Tiered Memory
- [ ] Module 05: Durability and LLM Gateway
- [ ] Module 06: Sandboxed Evals and Observability
- [ ] Module 07: Prefix Caching and Serving
- [ ] Module 08: Production Capstone Platform

---

## 6. Shipped Components and Architecture

### Module 01: Raw ReAct Agent Loop
- **Safe Tool Registry (`modules/01_raw_loop/src/tools.py`)**: Automatic OpenAI function calling JSON schema generation from Python type hints and docstrings.
- **Deterministic Tools**:
  - `calculate`: Regex-whitelisted safe math evaluator.
  - `read_file`: Line-buffered file reader with context-window truncation.
  - `run_command`: Subprocess shell execution with 10s timeout and output limits.
- **Agent Loop (`modules/01_raw_loop/src/agent.py`)**:
  - Pure Python while-loop without external agent framework bloat.
  - Pydantic serialization via `model_dump(exclude_none=True)` for tool calls.
  - Closed-loop error feedback: catches `JSONDecodeError` and execution exceptions, returning them as observations for self-correction.
  - Strict system prompt contract to enforce concise, non-conversational engineering responses.
- **Centralized Terminal UI (`shared/console.py`)**: Reusable terminal formatting across all modules with colorized turn traces, tool dispatches, observations, and rendered Markdown tables.
- **Test Suite (`modules/01_raw_loop/tests/test_loop.py`)**: 100% passing tests for tool schemas, safe execution, and error boundaries.

