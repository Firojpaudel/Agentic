"""
Module 02: Orchestration Engine Graph Assembly.
Ties together Triage Router, Domain Specialists, and HITL Checkpoints.
"""
from __future__ import annotations

try:
    from .graph import StateGraph, CompiledGraph
    from .state import NodeName
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
    from state import NodeName
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
    graph = StateGraph(entry_node=NodeName.TRIAGE)

    # Register specialist nodes
    graph.add_node(NodeName.TRIAGE, triage_router_node)
    graph.add_node(NodeName.APPOINTMENT_SPECIALIST, appointment_specialist_node)
    graph.add_node(NodeName.TICKETING_SPECIALIST, ticketing_specialist_node)
    graph.add_node(NodeName.GENERAL_HANDLER, general_handler_node)
    graph.add_node(NodeName.EXECUTE_ACTION, action_executor_node)
    graph.add_node(NodeName.HANDLE_REJECTION, rejection_handler_node)

    # Dynamic routing from triage based on classified intent
    graph.add_conditional_edge(NodeName.TRIAGE, route_by_intent)

    # Terminal transitions for leaf nodes
    graph.add_edge(NodeName.GENERAL_HANDLER, NodeName.END)
    graph.add_edge(NodeName.EXECUTE_ACTION, NodeName.END)
    graph.add_edge(NodeName.HANDLE_REJECTION, NodeName.END)
    graph.add_edge(NodeName.APPOINTMENT_SPECIALIST, NodeName.END)
    graph.add_edge(NodeName.TICKETING_SPECIALIST, NodeName.END)

    return graph.compile()

