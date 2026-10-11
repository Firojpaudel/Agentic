"""
Specialist Agent Nodes: Triage Router, Appointment Specialist, Ticketing Specialist,
Action Executor, and Rejection Handler.
"""
from __future__ import annotations

import re
from typing import Optional
try:
    from .state import (
        ActionProposal,
        AgentState,
        ApprovalStatus,
        IntentType,
        SeverityLevel,
    )
    from .domain_tools import hospital_scheduler, ticket_store
except ImportError:
    from state import (
        ActionProposal,
        AgentState,
        ApprovalStatus,
        IntentType,
        SeverityLevel,
    )
    from domain_tools import hospital_scheduler, ticket_store


# -----------------------------------------------------------------------------
# 1. Triage Router Node
# -----------------------------------------------------------------------------

def triage_router_node(state: AgentState) -> AgentState:
    """
    Classifies the user's latest query into an actionable domain intent.
    Routes to: appointment, ticketing, or general assistance.
    """
    latest_msg = state.get_latest_user_message().lower()

    # Check for Appointment Intent
    appointment_keywords = [
        "appointment", "doctor", "dr.", "schedule", "book", "slot",
        "availability", "clinic", "cardiology", "neurology", "medicine"
    ]
    # Check for Support / Ticketing Intent
    ticketing_keywords = [
        "ticket", "issue", "bug", "crash", "error", "outage", "monitor",
        "broken", "down", "support", "billing", "glitch", "escalate"
    ]

    if any(k in latest_msg for k in appointment_keywords):
        state.intent = IntentType.APPOINTMENT
        state.add_message("assistant", "Classified intent: APPOINTMENT. Handing off to Appointment Specialist.", name="triage")
    elif any(k in latest_msg for k in ticketing_keywords):
        state.intent = IntentType.TICKETING
        state.add_message("assistant", "Classified intent: TICKETING. Handing off to Ticketing Specialist.", name="triage")
    else:
        state.intent = IntentType.GENERAL
        state.add_message("assistant", "Classified intent: GENERAL. Routing to General Inquiry.", name="triage")

    return state


def route_by_intent(state: AgentState) -> str:
    """Conditional router edge evaluating state.intent."""
    if state.intent == IntentType.APPOINTMENT:
        return "appointment_specialist"
    elif state.intent == IntentType.TICKETING:
        return "ticketing_specialist"
    else:
        return "general_handler"


# -----------------------------------------------------------------------------
# 2. Appointment Specialist Node
# -----------------------------------------------------------------------------

def appointment_specialist_node(state: AgentState) -> AgentState:
    """
    Processes appointment availability queries and generates booking proposals.
    Any booking mutation triggers a pending ActionProposal requiring human approval.
    """
    latest_msg = state.get_latest_user_message()
    text = latest_msg.lower()

    # Extract date (YYYY-MM-DD) or default to 2026-10-15
    date_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else "2026-10-15"

    # Identify doctor
    doctor = "Dr. Sarah Chen"  # default
    if "marcus" in text or "vance" in text:
        doctor = "Dr. Marcus Vance"
    elif "elena" in text or "rostova" in text:
        doctor = "Dr. Elena Rostova"

    # Check if this is an explicit booking request or an availability query
    is_booking_request = any(w in text for w in ["book", "reserve", "schedule me", "confirm"])
    time_match = re.search(r"\b(\d{1,2}:\d{2})\b", text)

    # Patient name extraction (simple rule or fallback)
    patient_match = re.search(r"patient\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text, re.IGNORECASE)
    patient_name = patient_match.group(1).title() if patient_match else "Jane Doe"

    if is_booking_request and time_match:
        time = time_match.group(1)
        if len(time) == 4:  # e.g., 9:00 -> 09:00
            time = f"0{time}"

        # Check for scheduling conflict before proposing
        available_slots = hospital_scheduler.check_availability(doctor, date)
        if time not in available_slots:
            state.final_output = (
                f"Scheduling Conflict: {doctor} is not available on {date} at {time}. "
                f"Available open slots: {', '.join(available_slots) if available_slots else 'None'}."
            )
            state.add_message("assistant", state.final_output, name="appointment_specialist")
            return state

        # Create HITL Action Proposal
        proposal = ActionProposal(
            action_type="book_appointment",
            description=f"Book consultation for patient {patient_name} with {doctor} on {date} at {time}",
            parameters={
                "doctor": doctor,
                "date": date,
                "time": time,
                "patient": patient_name
            },
            status=ApprovalStatus.PENDING
        )
        state.pending_action = proposal
        state.add_message(
            "assistant",
            f"Action proposed: Booking slot for {patient_name} with {doctor} at {time} on {date}. "
            "Awaiting human approval before committing to database.",
            name="appointment_specialist"
        )
    else:
        # Standard availability check
        slots = hospital_scheduler.check_availability(doctor, date)
        slot_str = ", ".join(slots) if slots else "No slots available"
        state.final_output = f"Available slots for {doctor} on {date}: {slot_str}."
        state.add_message("assistant", state.final_output, name="appointment_specialist")

    return state


# -----------------------------------------------------------------------------
# 3. Ticketing Specialist Node
# -----------------------------------------------------------------------------

def ticketing_specialist_node(state: AgentState) -> AgentState:
    """
    Triage IT / medical device issues, assesses urgency, and files tickets.
    Critical and High severity issues require Human Approval.
    """
    latest_msg = state.get_latest_user_message()
    severity, rationale = ticket_store.classify_severity(latest_msg, latest_msg)

    # Determine category
    category = "General IT"
    text = latest_msg.lower()
    if any(k in text for k in ["cardiac", "patient", "monitor", "ventilator", "bedside"]):
        category = "Biomedical Engineering"
    elif any(k in text for k in ["billing", "invoice", "charge", "payment"]):
        category = "Hospital Billing"

    if severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
        # Critical action requiring human review before escalation
        proposal = ActionProposal(
            action_type="create_critical_ticket",
            description=f"File {severity.value.upper()} incident for '{latest_msg[:60]}...' under {category}",
            parameters={
                "title": latest_msg[:50],
                "description": latest_msg,
                "category": category,
                "severity": severity
            },
            status=ApprovalStatus.PENDING
        )
        state.pending_action = proposal
        state.add_message(
            "assistant",
            f"Urgent incident detected ({severity.value.upper()}). "
            f"Reason: {rationale} Action proposal created. Awaiting supervisor approval.",
            name="ticketing_specialist"
        )
    else:
        # Auto-create low/medium ticket directly
        ticket = ticket_store.create_ticket(
            title=latest_msg[:50],
            category=category,
            severity=severity,
            description=latest_msg
        )
        state.final_output = (
            f"Support ticket registered successfully: {ticket.ticket_id} "
            f"[{ticket.severity.value.upper()}] Assigned to: {ticket.assigned_to}."
        )
        state.add_message("assistant", state.final_output, name="ticketing_specialist")

    return state


# -----------------------------------------------------------------------------
# 4. Action Executor Node (Runs when approved)
# -----------------------------------------------------------------------------

def action_executor_node(state: AgentState) -> AgentState:
    """
    Executes sensitive actions following human approval.
    """
    proposal = state.pending_action
    if not proposal:
        state.final_output = "No pending action found to execute."
        return state

    if proposal.action_type == "book_appointment":
        params = proposal.parameters
        res = hospital_scheduler.book_slot(
            doctor_name=params["doctor"],
            date=params["date"],
            time=params["time"],
            patient_name=params["patient"]
        )
        if res.get("success"):
            state.final_output = (
                f"Booking Confirmed: {res['booking_ref']} | Patient: {res['patient']} | "
                f"Doctor: {res['doctor']} ({res['department']}) | Date: {res['date']} at {res['time']}."
            )
        else:
            state.final_output = f"Execution Failed: {res.get('error')}"

    elif proposal.action_type == "create_critical_ticket":
        params = proposal.parameters
        ticket = ticket_store.create_ticket(
            title=params["title"],
            category=params["category"],
            severity=params["severity"],
            description=params["description"],
            assigned_to="Critical Incident Response Team (Level 3)"
        )
        state.final_output = (
            f"Critical Ticket Escalated: {ticket.ticket_id} [{ticket.severity.value.upper()}] | "
            f"Assigned to: {ticket.assigned_to}. Notification dispatched."
        )
    else:
        state.final_output = f"Executed generic action: {proposal.action_type}"

    # Clear pending action after successful execution
    state.add_message("assistant", state.final_output, name="action_executor")
    state.pending_action = None
    state.is_completed = True
    return state


# -----------------------------------------------------------------------------
# 5. Rejection Handler Node (Runs when rejected)
# -----------------------------------------------------------------------------

def rejection_handler_node(state: AgentState) -> AgentState:
    """
    Handles rejected action proposals and incorporates human reviewer feedback.
    """
    proposal = state.pending_action
    feedback = proposal.reviewer_notes if proposal else "No feedback provided."
    state.final_output = (
        f"Action Canceled: The proposed action '{proposal.action_type if proposal else 'N/A'}' was rejected by the reviewer. "
        f"Feedback: {feedback}"
    )
    state.add_message("assistant", state.final_output, name="rejection_handler")
    state.pending_action = None
    state.is_completed = True
    return state


# -----------------------------------------------------------------------------
# 6. General Handler Node
# -----------------------------------------------------------------------------

def general_handler_node(state: AgentState) -> AgentState:
    """Handles general clinical directories and help inquiries."""
    doctors = hospital_scheduler.list_doctors()
    doc_lines = [f"- {d['doctor']} ({d['department']})" for d in doctors]
    state.final_output = (
        "Welcome to Hospital Central Services.\n\n"
        "Available Specialists:\n" + "\n".join(doc_lines) + "\n\n"
        "How may I assist you today? (e.g. 'Check availability for Dr. Sarah Chen' or 'Report an outage')"
    )
    state.add_message("assistant", state.final_output, name="general_handler")
    state.is_completed = True
    return state
