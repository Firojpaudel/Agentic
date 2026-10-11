"""
Interactive Demonstration Runner for Module 02: Orchestration & State Graphs.
Runs scenarios with live Rich terminal styling and Human-in-the-Loop workflows.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root and module src to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "modules" / "02_orchestration" / "src"))

from shared.console import agent_console
from state import AgentState, ApprovalStatus
from engine import create_orchestration_graph
from benchmark import benchmark_overhead


def run_interactive_demo():
    graph = create_orchestration_graph()

    agent_console.print_task(
        "Module 02: Multi-Agent Clinical Orchestrator & State Graph\n"
        "Features: Triage Routing, Specialist Handoffs, and Human-in-the-Loop Checkpoints",
        title="Module 02 Demonstration"
    )

    # -------------------------------------------------------------------------
    # Scenario 1: Doctor Availability Query (Zero-interruption flow)
    # -------------------------------------------------------------------------
    agent_console.print_task(
        "User: Can I check available slots for Dr. Sarah Chen on 2026-10-15?",
        title="Scenario 1: Non-Mutating Inquiry"
    )
    state1 = AgentState()
    state1.add_message("user", "Can I check available slots for Dr. Sarah Chen on 2026-10-15?")
    res1, interrupted1 = graph.run(state1)
    
    agent_console.print_solution(
        f"**Intent**: `{res1.intent.value}`\n\n"
        f"**Transitions**: {' -> '.join([t.split(': ')[1] for t in res1.transition_history])}\n\n"
        f"**Response**:\n{res1.final_output}",
        title="Scenario 1 Output"
    )

    # -------------------------------------------------------------------------
    # Scenario 2: Mutating Booking with Human Approval Checkpoint
    # -------------------------------------------------------------------------
    prompt2 = "Book Dr. Sarah Chen on 2026-10-15 at 09:00 for patient Mark Peterson"
    agent_console.print_task(prompt2, title="Scenario 2: Mutating Booking (HITL Required)")

    state2 = AgentState()
    state2.add_message("user", prompt2)
    paused_state, is_interrupted = graph.run(state2)

    if is_interrupted and paused_state.pending_action:
        proposal = paused_state.pending_action
        agent_console.print_error(
            f"GRAPH PAUSED at Checkpoint [Session: {paused_state.session_id}]\n"
            f"Action: {proposal.action_type}\n"
            f"Details: {proposal.description}\n"
            f"Parameters: {proposal.parameters}\n"
            f"Status: {proposal.status.value.upper()}",
            title="HUMAN-IN-THE-LOOP APPROVAL CHECKPOINT"
        )

        # Simulate Human Supervisor Approval
        agent_console.print_task(
            "Supervisor Action: [APPROVED] - 'Medical record confirmed; insurance verified.'",
            title="Human Supervisor Decision"
        )
        resumed_state, _ = graph.resume(
            session_id=paused_state.session_id,
            approved=True,
            reviewer_notes="Medical record confirmed; insurance verified."
        )

        agent_console.print_solution(
            f"**Transitions**: {' -> '.join([t.split(': ')[1] for t in resumed_state.transition_history])}\n\n"
            f"**Result**:\n{resumed_state.final_output}",
            title="Scenario 2 Completed"
        )

    # -------------------------------------------------------------------------
    # Scenario 3: Critical Biomedical Incident Triage
    # -------------------------------------------------------------------------
    prompt3 = "CRITICAL: Cardiac telemetry monitor power failure in ICU Station 2"
    agent_console.print_task(prompt3, title="Scenario 3: Critical Support Incident")

    state3 = AgentState()
    state3.add_message("user", prompt3)
    paused3, is_interrupted3 = graph.run(state3)

    if is_interrupted3 and paused3.pending_action:
        prop3 = paused3.pending_action
        agent_console.print_error(
            f"CRITICAL ESCALATION PROPOSAL\n"
            f"Action: {prop3.action_type}\n"
            f"Severity: HIGH / CRITICAL\n"
            f"Details: {prop3.description}",
            title="SUPERVISOR ESCALATION GATEWAY"
        )

        resumed3, _ = graph.resume(
            session_id=paused3.session_id,
            approved=True,
            reviewer_notes="Verified by On-Call Chief Medical Officer"
        )

        agent_console.print_solution(
            f"**Transitions**: {' -> '.join([t.split(': ')[1] for t in resumed3.transition_history])}\n\n"
            f"**Escalation Result**:\n{resumed3.final_output}",
            title="Scenario 3 Escalated"
        )

    # -------------------------------------------------------------------------
    # Scenario 4: Latency Benchmark
    # -------------------------------------------------------------------------
    agent_console.print_task("Benchmarking StateGraph transition latency overhead...", title="Scenario 4: Performance Benchmark")
    bench = benchmark_overhead(iterations=500)
    agent_console.print_solution(
        f"- **Iterations**: {bench['iterations']}\n"
        f"- **Raw Procedural Loop (avg)**: {bench['raw_avg_microseconds']} µs\n"
        f"- **Typed StateGraph (avg)**: {bench['graph_avg_microseconds']} µs\n"
        f"- **Transition Overhead**: {bench['overhead_microseconds']} µs (~{bench['overhead_ratio']}x)\n\n"
        "> Graph overhead is on the microsecond scale, completely negligible compared to network I/O and LLM token generation (100–500ms).",
        title="Benchmark Summary"
    )


if __name__ == "__main__":
    run_interactive_demo()
