"""
Module 02: Deterministic StateGraph Engine & Checkpointer.
First-principles implementation of directed graphs, conditional transitions,
and Human-in-the-Loop (HITL) interruptible checkpoints.
"""
from __future__ import annotations

import copy
from typing import Callable, Dict, List, Optional, Tuple
try:
    from .state import AgentState, ApprovalStatus
except ImportError:
    from state import AgentState, ApprovalStatus


NodeFunc = Callable[[AgentState], AgentState]
RouterFunc = Callable[[AgentState], str]


class StateGraph:
    """
    Directed state graph with conditional branch routing and checkpointing.
    Implements the explicit state-machine pattern without hiding mechanics.
    """

    def __init__(self, entry_node: str = "triage"):
        self.entry_node: str = entry_node
        self.nodes: Dict[str, NodeFunc] = {}
        self.conditional_edges: Dict[str, RouterFunc] = {}
        self.fixed_edges: Dict[str, str] = {}
        self.checkpoints: Dict[str, AgentState] = {}

    def add_node(self, name: str, func: NodeFunc) -> StateGraph:
        """Register a node function with an associated name."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists in graph.")
        self.nodes[name] = func
        return self

    def add_edge(self, source: str, target: str) -> StateGraph:
        """Add a deterministic transition edge from source to target."""
        self.fixed_edges[source] = target
        return self

    def add_conditional_edge(self, source: str, router: RouterFunc) -> StateGraph:
        """Add a dynamic routing edge governed by a router function."""
        self.conditional_edges[source] = router
        return self

    def compile(self) -> CompiledGraph:
        """Validate topology and return executable compiled graph."""
        if self.entry_node not in self.nodes:
            raise ValueError(f"Entry node '{self.entry_node}' is not registered.")
        return CompiledGraph(self)


class CompiledGraph:
    """Executable compiled instance of StateGraph with step execution & HITL checkpointing."""

    def __init__(self, graph: StateGraph):
        self.graph: StateGraph = graph

    def run(
        self,
        initial_state: AgentState,
        max_steps: int = 15
    ) -> Tuple[AgentState, bool]:
        """
        Execute graph until termination ('__end__'), step limit, or HITL interruption.
        Returns: (state, is_interrupted)
        """
        state = copy.deepcopy(initial_state)
        current = state.current_node or self.graph.entry_node
        steps = 0

        while steps < max_steps:
            steps += 1

            if current == "__end__":
                state.is_completed = True
                state.log_transition("__end__")
                return state, False

            if current not in self.graph.nodes:
                state.add_message("system", f"Runtime Error: Node '{current}' not found in graph.")
                state.is_completed = True
                return state, False

            # Execute node
            node_fn = self.graph.nodes[current]
            state.log_transition(current)
            state = node_fn(state)

            # Check for Human-in-the-Loop interruption
            if state.pending_action and state.pending_action.status == ApprovalStatus.PENDING:
                # Save checkpoint in state registry
                self.graph.checkpoints[state.session_id] = copy.deepcopy(state)
                return state, True  # Interrupted for human review

            # Determine next transition
            if current in self.graph.conditional_edges:
                current = self.graph.conditional_edges[current](state)
            elif current in self.graph.fixed_edges:
                current = self.graph.fixed_edges[current]
            else:
                # Default to completion if no edges defined
                current = "__end__"

        state.add_message("system", f"Exceeded maximum execution steps ({max_steps}).")
        state.is_completed = True
        return state, False

    def resume(
        self,
        session_id: str,
        approved: bool,
        reviewer_notes: Optional[str] = None
    ) -> Tuple[AgentState, bool]:
        """
        Resume execution of a paused checkpoint with human approval / rejection.
        """
        if session_id not in self.graph.checkpoints:
            raise KeyError(f"No active checkpoint found for session '{session_id}'.")

        state = copy.deepcopy(self.graph.checkpoints[session_id])
        if not state.pending_action:
            raise ValueError(f"Session '{session_id}' has no pending action to review.")

        # Update proposal status
        state.pending_action.status = (
            ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        )
        state.pending_action.reviewer_notes = reviewer_notes

        # Route after human decision
        if approved:
            # Transition to action executor node
            state.current_node = "execute_action"
        else:
            # Transition to correction / rejection handler
            state.current_node = "handle_rejection"

        # Resume execution loop
        return self.run(state)
