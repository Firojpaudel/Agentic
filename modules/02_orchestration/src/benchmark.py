"""
Module 02: Latency & Framework Overhead Benchmark.
Measures the computational overhead of typed StateGraph transitions
versus raw procedural execution.
"""
from __future__ import annotations

import time
from typing import Dict, Any
try:
    from .state import AgentState, IntentType
    from .engine import create_orchestration_graph
except ImportError:
    from state import AgentState, IntentType
    from engine import create_orchestration_graph


def run_raw_procedural_loop(query: str) -> Dict[str, Any]:
    """Baseline raw procedural router and handler without state graph structures."""
    q = query.lower()
    if "doctor" in q or "appointment" in q:
        intent = "appointment"
        output = "Checking appointments"
    elif "ticket" in q or "issue" in q:
        intent = "ticketing"
        output = "Handling ticket"
    else:
        intent = "general"
        output = "General inquiry"
    return {"intent": intent, "output": output}


def benchmark_overhead(iterations: int = 1000) -> Dict[str, float]:
    """Run comparative benchmark between raw loop and compiled StateGraph."""
    query = "Check availability for Dr. Sarah Chen on 2026-10-15"
    graph = create_orchestration_graph()

    # 1. Benchmark Raw Procedural Loop
    start_raw = time.perf_counter()
    for _ in range(iterations):
        _ = run_raw_procedural_loop(query)
    raw_duration_sec = time.perf_counter() - start_raw
    raw_avg_us = (raw_duration_sec / iterations) * 1_000_000

    # 2. Benchmark Typed StateGraph Execution
    start_graph = time.perf_counter()
    for _ in range(iterations):
        state = AgentState()
        state.add_message("user", query)
        # Run graph (availability check terminates directly without HITL)
        res_state, _ = graph.run(state)
    graph_duration_sec = time.perf_counter() - start_graph
    graph_avg_us = (graph_duration_sec / iterations) * 1_000_000

    overhead_us = graph_avg_us - raw_avg_us
    overhead_ratio = graph_avg_us / raw_avg_us if raw_avg_us > 0 else 1.0

    return {
        "iterations": iterations,
        "raw_avg_microseconds": round(raw_avg_us, 2),
        "graph_avg_microseconds": round(graph_avg_us, 2),
        "overhead_microseconds": round(overhead_us, 2),
        "overhead_ratio": round(overhead_ratio, 2),
    }


if __name__ == "__main__":
    results = benchmark_overhead(iterations=1000)
    print("=" * 60)
    print("  Framework Overhead Benchmark (Module 02 vs Raw Baseline)")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {k:30}: {v}")
    print("=" * 60)
