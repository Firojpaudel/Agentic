"""
Module 02: Unit Tests for StateGraph, Specialists, and HITL Checkpoints.
100% deterministic, zero-cost, offline execution.
"""
import sys
from pathlib import Path
import pytest

# Add module's src directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from state import AgentState, IntentType, ApprovalStatus, SeverityLevel
from graph import StateGraph
from engine import create_orchestration_graph
from domain_tools import HospitalScheduler, TicketStore


def test_triage_routing_appointment():
    graph = create_orchestration_graph()
    state = AgentState()
    state.add_message("user", "Can I check available appointment slots for Dr. Sarah Chen?")
    
    final_state, interrupted = graph.run(state)
    assert final_state.intent == IntentType.APPOINTMENT
    assert not interrupted
    assert "Dr. Sarah Chen" in (final_state.final_output or "")
    assert "09:00" in (final_state.final_output or "")


def test_triage_routing_ticketing():
    graph = create_orchestration_graph()
    state = AgentState()
    state.add_message("user", "We have a glitch in the portal formatting.")
    
    final_state, interrupted = graph.run(state)
    assert final_state.intent == IntentType.TICKETING
    assert not interrupted
    assert "Support ticket registered successfully" in (final_state.final_output or "")


def test_triage_routing_general():
    graph = create_orchestration_graph()
    state = AgentState()
    state.add_message("user", "Hello, what departments are in this hospital?")
    
    final_state, interrupted = graph.run(state)
    assert final_state.intent == IntentType.GENERAL
    assert not interrupted
    assert "Available Specialists" in (final_state.final_output or "")


def test_appointment_conflict_detection():
    graph = create_orchestration_graph()
    state = AgentState()
    # 10:00 on 2026-10-15 is pre-booked by John Doe in our mock database
    state.add_message("user", "Book appointment with Dr. Sarah Chen on 2026-10-15 at 10:00 for patient Alice")
    
    final_state, interrupted = graph.run(state)
    assert not interrupted
    assert "Scheduling Conflict" in (final_state.final_output or "")
    assert "is not available" in (final_state.final_output or "")
    assert final_state.pending_action is None


def test_hitl_appointment_proposal_and_approval():
    graph = create_orchestration_graph()
    state = AgentState()
    # 09:00 is an open slot
    state.add_message("user", "Please book Dr. Sarah Chen on 2026-10-15 at 09:00 for patient Alice Smith")
    
    paused_state, is_interrupted = graph.run(state)
    assert is_interrupted is True
    assert paused_state.pending_action is not None
    assert paused_state.pending_action.action_type == "book_appointment"
    assert paused_state.pending_action.status == ApprovalStatus.PENDING
    assert paused_state.pending_action.parameters["time"] == "09:00"

    # Human Supervisor Approves
    resumed_state, still_interrupted = graph.resume(
        session_id=paused_state.session_id,
        approved=True,
        reviewer_notes="Verified patient insurance active"
    )
    assert still_interrupted is False
    assert resumed_state.is_completed is True
    assert "Booking Confirmed" in (resumed_state.final_output or "")
    assert resumed_state.pending_action is None


def test_hitl_appointment_rejection():
    graph = create_orchestration_graph()
    state = AgentState()
    state.add_message("user", "Book Dr. Sarah Chen on 2026-10-15 at 14:00 for patient Bob")
    
    paused_state, is_interrupted = graph.run(state)
    assert is_interrupted is True

    # Human Supervisor Rejects
    resumed_state, _ = graph.resume(
        session_id=paused_state.session_id,
        approved=False,
        reviewer_notes="Doctor is called into emergency surgery at 14:00"
    )
    assert "Action Canceled" in (resumed_state.final_output or "")
    assert "emergency surgery" in (resumed_state.final_output or "")
    assert resumed_state.pending_action is None


def test_hitl_critical_ticketing_escalation():
    graph = create_orchestration_graph()
    state = AgentState()
    state.add_message("user", "CRITICAL: Cardiac monitor failure in ICU Room 4, telemetry down!")
    
    paused_state, is_interrupted = graph.run(state)
    assert is_interrupted is True
    assert paused_state.pending_action is not None
    assert paused_state.pending_action.action_type == "create_critical_ticket"
    assert paused_state.pending_action.status == ApprovalStatus.PENDING

    # Reviewer Approves Critical Escalation
    resumed_state, _ = graph.resume(
        session_id=paused_state.session_id,
        approved=True,
        reviewer_notes="Verified by ICU head nurse"
    )
    assert "Critical Ticket Escalated" in (resumed_state.final_output or "")
    assert "Critical Incident Response Team" in (resumed_state.final_output or "")


def test_max_steps_guard():
    # Build graph with intentional infinite loop to test safety guard
    g = StateGraph(entry_node="loop_a")
    g.add_node("loop_a", lambda s: s)
    g.add_node("loop_b", lambda s: s)
    g.add_edge("loop_a", "loop_b")
    g.add_edge("loop_b", "loop_a")
    compiled = g.compile()

    state = AgentState()
    res, interrupted = compiled.run(state, max_steps=4)
    assert not interrupted
    assert res.is_completed is True
    assert "Exceeded maximum execution steps" in res.messages[-1].content
