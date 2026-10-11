"""
Specialist Agent Nodes: Triage Router, Appointment Specialist, Ticketing Specialist,
Action Executor, and Rejection Handler.
Grounded in:
- openai/openai-agents-python (Swarm handoffs and mutating action guardrails)
- pydantic/pydantic-ai (Typed contracts and dependency injection)
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict
try:
    from .state import (
        ActionProposal,
        ActionType,
        AgentState,
        ApprovalStatus,
        IntentType,
        NodeName,
        Role,
        SeverityLevel,
        TicketCategory,
    )
    from .domain_tools import hospital_scheduler, ticket_store
except ImportError:
    from state import (
        ActionProposal,
        ActionType,
        AgentState,
        ApprovalStatus,
        IntentType,
        NodeName,
        Role,
        SeverityLevel,
        TicketCategory,
    )
    from domain_tools import hospital_scheduler, ticket_store


# -----------------------------------------------------------------------------
# 1. Routing & Intent Classification
# -----------------------------------------------------------------------------

APPOINTMENT_KEYWORDS = (
    "appointment", "doctor", "dr.", "schedule", "book", "slot",
    "availability", "clinic", "cardiology", "neurology", "medicine"
)

TICKETING_KEYWORDS = (
    "ticket", "issue", "bug", "crash", "error", "outage", "monitor",
    "broken", "down", "support", "billing", "glitch", "escalate"
)

INTENT_ROUTER_MAP: Dict[IntentType, str] = {
    IntentType.APPOINTMENT: NodeName.APPOINTMENT_SPECIALIST,
    IntentType.TICKETING: NodeName.TICKETING_SPECIALIST,
}


def triage_router_node(state: AgentState) -> AgentState:
    """
    Classifies the user's latest query into an actionable domain intent.
    Routes to: appointment, ticketing, or general assistance.
    """
    latest_msg = state.get_latest_user_message().lower()

    if any(k in latest_msg for k in APPOINTMENT_KEYWORDS):
        state.intent = IntentType.APPOINTMENT
        state.add_message(Role.ASSISTANT, "Classified intent: APPOINTMENT. Handing off to Appointment Specialist.", name=NodeName.TRIAGE)
        return state

    if any(k in latest_msg for k in TICKETING_KEYWORDS):
        state.intent = IntentType.TICKETING
        state.add_message(Role.ASSISTANT, "Classified intent: TICKETING. Handing off to Ticketing Specialist.", name=NodeName.TRIAGE)
        return state

    state.intent = IntentType.GENERAL
    state.add_message(Role.ASSISTANT, "Classified intent: GENERAL. Routing to General Inquiry.", name=NodeName.TRIAGE)
    return state


def route_by_intent(state: AgentState) -> str:
    """Conditional router edge evaluating state.intent in O(1)."""
    return INTENT_ROUTER_MAP.get(state.intent, NodeName.GENERAL_HANDLER)


# -----------------------------------------------------------------------------
# 2. Appointment Specialist Node
# -----------------------------------------------------------------------------

DOCTOR_ALIASES = {
    ("marcus", "vance"): "Dr. Marcus Vance",
    ("elena", "rostova"): "Dr. Elena Rostova",
    ("sarah", "chen"): "Dr. Sarah Chen",
}


def _resolve_doctor(text: str) -> str:
    """Resolve doctor name from query text with O(1) keyword scan."""
    for aliases, doc_name in DOCTOR_ALIASES.items():
        if any(alias in text for alias in aliases):
            return doc_name
    return "Dr. Sarah Chen"


def appointment_specialist_node(state: AgentState) -> AgentState:
    """
    Processes appointment availability queries and generates booking proposals.
    Any booking mutation triggers a pending ActionProposal requiring human approval.
    """
    latest_msg = state.get_latest_user_message()
    text = latest_msg.lower()

    # Extract date (YYYY-MM-DD) or default to standard simulation date
    date_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else "2026-10-15"
    doctor = _resolve_doctor(text)

    is_booking_request = any(w in text for w in ["book", "reserve", "schedule me", "confirm"])
    time_match = re.search(r"\b(\d{1,2}:\d{2})\b", text)

    # Guard clause: non-booking queries return availability directly
    if not (is_booking_request and time_match):
        slots = hospital_scheduler.check_availability(doctor, date)
        slot_str = ", ".join(slots) if slots else "No slots available"
        state.final_output = f"Available slots for {doctor} on {date}: {slot_str}."
        state.add_message(Role.ASSISTANT, state.final_output, name=NodeName.APPOINTMENT_SPECIALIST)
        return state

    # Extract slot time and patient name
    time = time_match.group(1).zfill(5)
    patient_match = re.search(r"patient\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text, re.IGNORECASE)
    patient_name = patient_match.group(1).title() if patient_match else "Jane Doe"

    # Guard clause: detect scheduling conflicts before proposal creation
    available_slots = hospital_scheduler.check_availability(doctor, date)
    if time not in available_slots:
        state.final_output = (
            f"Scheduling Conflict: {doctor} is not available on {date} at {time}. "
            f"Available open slots: {', '.join(available_slots) if available_slots else 'None'}."
        )
        state.add_message(Role.ASSISTANT, state.final_output, name=NodeName.APPOINTMENT_SPECIALIST)
        return state

    # Create HITL Action Proposal (Interruption gateway)
    state.pending_action = ActionProposal(
        action_type=ActionType.BOOK_APPOINTMENT,
        description=f"Book consultation for patient {patient_name} with {doctor} on {date} at {time}",
        parameters={
            "doctor": doctor,
            "date": date,
            "time": time,
            "patient": patient_name,
        },
        status=ApprovalStatus.PENDING,
    )
    state.add_message(
        Role.ASSISTANT,
        f"Action proposed: Booking slot for {patient_name} with {doctor} at {time} on {date}. "
        "Awaiting human approval before committing to database.",
        name=NodeName.APPOINTMENT_SPECIALIST,
    )
    return state


# -----------------------------------------------------------------------------
# 3. Ticketing Specialist Node
# -----------------------------------------------------------------------------

def _resolve_ticket_category(text: str) -> str:
    """Determine ticket category using keyword matching."""
    t = text.lower()
    if any(k in t for k in ["cardiac", "patient", "monitor", "ventilator", "bedside"]):
        return TicketCategory.BIOMEDICAL
    if any(k in t for k in ["billing", "invoice", "charge", "payment"]):
        return TicketCategory.BILLING
    return TicketCategory.GENERAL_IT


def ticketing_specialist_node(state: AgentState) -> AgentState:
    """
    Triage IT / medical device issues, assesses urgency, and files tickets.
    Critical and High severity issues require Human Approval.
    """
    latest_msg = state.get_latest_user_message()
    severity, rationale = ticket_store.classify_severity(latest_msg, latest_msg)
    category = _resolve_ticket_category(latest_msg)

    # Guard clause: Low / Medium severity auto-creates ticket directly
    if severity not in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
        ticket = ticket_store.create_ticket(
            title=latest_msg[:50],
            category=category,
            severity=severity,
            description=latest_msg,
        )
        state.final_output = (
            f"Support ticket registered successfully: {ticket.ticket_id} "
            f"[{ticket.severity.value.upper()}] Assigned to: {ticket.assigned_to}."
        )
        state.add_message(Role.ASSISTANT, state.final_output, name=NodeName.TICKETING_SPECIALIST)
        return state

    # High / Critical severity requires supervisor review before escalation
    state.pending_action = ActionProposal(
        action_type=ActionType.CREATE_CRITICAL_TICKET,
        description=f"File {severity.value.upper()} incident for '{latest_msg[:60]}...' under {category}",
        parameters={
            "title": latest_msg[:50],
            "description": latest_msg,
            "category": category,
            "severity": severity,
        },
        status=ApprovalStatus.PENDING,
    )
    state.add_message(
        Role.ASSISTANT,
        f"Urgent incident detected ({severity.value.upper()}). "
        f"Reason: {rationale} Action proposal created. Awaiting supervisor approval.",
        name=NodeName.TICKETING_SPECIALIST,
    )
    return state


# -----------------------------------------------------------------------------
# 4. Action Execution Dispatcher Map (O(1))
# -----------------------------------------------------------------------------

def _execute_appointment_booking(params: Dict[str, Any]) -> str:
    res = hospital_scheduler.book_slot(
        doctor_name=params["doctor"],
        date=params["date"],
        time=params["time"],
        patient_name=params["patient"],
    )
    if res.get("success"):
        return (
            f"Booking Confirmed: {res['booking_ref']} | Patient: {res['patient']} | "
            f"Doctor: {res['doctor']} ({res['department']}) | Date: {res['date']} at {res['time']}."
        )
    return f"Execution Failed: {res.get('error')}"


def _execute_critical_ticket(params: Dict[str, Any]) -> str:
    ticket = ticket_store.create_ticket(
        title=params["title"],
        category=params["category"],
        severity=params["severity"],
        description=params["description"],
        assigned_to="Critical Incident Response Team (Level 3)",
    )
    return (
        f"Critical Ticket Escalated: {ticket.ticket_id} [{ticket.severity.value.upper()}] | "
        f"Assigned to: {ticket.assigned_to}. Notification dispatched."
    )


ACTION_DISPATCH_MAP: Dict[str, Callable[[Dict[str, Any]], str]] = {
    ActionType.BOOK_APPOINTMENT: _execute_appointment_booking,
    ActionType.CREATE_CRITICAL_TICKET: _execute_critical_ticket,
}


def action_executor_node(state: AgentState) -> AgentState:
    """Executes sensitive actions following human approval via O(1) dispatcher."""
    proposal = state.pending_action
    if not proposal:
        state.final_output = "No pending action found to execute."
        return state

    handler = ACTION_DISPATCH_MAP.get(proposal.action_type)
    state.final_output = (
        handler(proposal.parameters)
        if handler
        else f"Executed generic action: {proposal.action_type}"
    )

    state.add_message(Role.ASSISTANT, state.final_output, name=NodeName.EXECUTE_ACTION)
    state.pending_action = None
    state.is_completed = True
    return state


# -----------------------------------------------------------------------------
# 5. Rejection Handler Node
# -----------------------------------------------------------------------------

def rejection_handler_node(state: AgentState) -> AgentState:
    """Handles rejected action proposals and incorporates human reviewer feedback."""
    proposal = state.pending_action
    action_name = proposal.action_type if proposal else "N/A"
    feedback = proposal.reviewer_notes if proposal and proposal.reviewer_notes else "No feedback provided."

    state.final_output = (
        f"Action Canceled: The proposed action '{action_name}' was rejected by the reviewer. "
        f"Feedback: {feedback}"
    )
    state.add_message(Role.ASSISTANT, state.final_output, name=NodeName.HANDLE_REJECTION)
    state.pending_action = None
    state.is_completed = True
    return state


# -----------------------------------------------------------------------------
# 6. General Handler Node
# -----------------------------------------------------------------------------

def general_handler_node(state: AgentState) -> AgentState:
    """Handles general clinical directories and directory inquiries."""
    doctors = hospital_scheduler.list_doctors()
    doc_lines = [f"- {d['doctor']} ({d['department']})" for d in doctors]
    state.final_output = (
        "Welcome to Hospital Central Services.\n\n"
        "Available Specialists:\n" + "\n".join(doc_lines) + "\n\n"
        "How may I assist you today? (e.g. 'Check availability for Dr. Sarah Chen' or 'Report an outage')"
    )
    state.add_message(Role.ASSISTANT, state.final_output, name=NodeName.GENERAL_HANDLER)
    state.is_completed = True
    return state
