"""
Module 02: Orchestration Engine Graph Assembly.
Ties together Triage Router, Domain Specialists, and HITL Checkpoints.
"""
from __future__ import annotations

try:
    from .graph import StateGraph, CompiledGraph
    from .specialists import (
        triage_router_node,
        route_by_intent,
        appointment_specialist_node,
        ticketing_specialist_node,
        general_handler_node,
        action_executor_node,
        rejection_handler_node,
    )
except ImportError:
    from graph import StateGraph, CompiledGraph
    from specialists import (
        triage_router_node,
        route_by_intent,
        appointment_specialist_node,
        ticketing_specialist_node,
        general_handler_node,
        action_executor_node,
        rejection_handler_node,
    )


def create_orchestration_graph() -> CompiledGraph:
    """Build and compile the multi-agent clinical orchestration graph."""
    graph = StateGraph(entry_node="triage")

    # Register nodes
    graph.add_node("triage", triage_router_node)
    graph.add_node("appointment_specialist", appointment_specialist_node)
    graph.add_node("ticketing_specialist", ticketing_specialist_node)
    graph.add_node("general_handler", general_handler_node)
    graph.add_node("execute_action", action_executor_node)
    graph.add_node("handle_rejection", rejection_handler_node)

    # Routing from triage
    graph.add_conditional_edge("triage", route_by_intent)

    # Terminal transitions for leaves
    graph.add_edge("general_handler", "__end__")
    graph.add_edge("execute_action", "__end__")
    graph.add_edge("handle_rejection", "__end__")
    graph.add_edge("appointment_specialist", "__end__")
    graph.add_edge("ticketing_specialist", "__end__")

    return graph.compile()
