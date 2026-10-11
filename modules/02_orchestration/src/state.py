"""
Module 02: Typed State Contracts and Action Schemas.
Grounded in open-source reference implementations:
- pydantic/pydantic-ai (Typed contracts, strict schema validation, dependency injection)
- langchain-ai/langgraph (Stateful graphs, checkpoint persistence, interruptibility)
- openai/openai-agents-python (Swarm handoffs and mutating guardrail primitives)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Classified user intent handled by the router."""
    APPOINTMENT = "appointment"
    TICKETING = "ticketing"
    GENERAL = "general"
    UNKNOWN = "unknown"


class ApprovalStatus(str, Enum):
    """Lifecycle of a sensitive action proposal."""
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SeverityLevel(str, Enum):
    """Urgency level for ticketing domain."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Role(str, Enum):
    """Dialogue message role."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ActionType(str, Enum):
    """Domain action types requiring execution or review."""
    BOOK_APPOINTMENT = "book_appointment"
    CREATE_CRITICAL_TICKET = "create_critical_ticket"


class NodeName(str, Enum):
    """StateGraph node identifiers."""
    TRIAGE = "triage"
    APPOINTMENT_SPECIALIST = "appointment_specialist"
    TICKETING_SPECIALIST = "ticketing_specialist"
    GENERAL_HANDLER = "general_handler"
    EXECUTE_ACTION = "execute_action"
    HANDLE_REJECTION = "handle_rejection"
    END = "__end__"


class TicketCategory(str, Enum):
    """Categorization for hospital support tickets."""
    GENERAL_IT = "General IT"
    BIOMEDICAL = "Biomedical Engineering"
    BILLING = "Hospital Billing"


class Message(BaseModel):
    """Structured dialogue message."""
    role: str = Field(description="Message role: system, user, assistant, or tool")
    content: str = Field(description="Textual payload of the message")
    name: Optional[str] = Field(default=None, description="Sender identifier or node name")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO-8601 timestamp"
    )


class ActionProposal(BaseModel):
    """
    Contract for a high-risk or mutating action requiring
    human approval before execution (e.g. database commit, payment, ticket creation).
    """
    proposal_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique identifier for the action proposal"
    )
    action_type: str = Field(description="Action name (e.g., 'book_appointment', 'create_critical_ticket')")
    description: str = Field(description="Human-readable explanation of what will be performed")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution arguments")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    reviewer_notes: Optional[str] = Field(default=None, description="Feedback from human reviewer")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when proposal was generated"
    )


class AppointmentSlot(BaseModel):
    """Representation of a doctor's calendar slot."""
    doctor_name: str
    department: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    is_available: bool = True
    patient_name: Optional[str] = None


class Ticket(BaseModel):
    """Support or medical escalation ticket."""
    ticket_id: str = Field(default_factory=lambda: f"TCK-{str(uuid.uuid4())[:6].upper()}")
    title: str
    category: str
    severity: SeverityLevel
    description: str
    status: str = "OPEN"
    assigned_to: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentState(BaseModel):
    """
    Single source of truth for the Orchestration State Graph.
    Passed between nodes and checkpoints.
    """
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique session identifier"
    )
    current_node: Optional[str] = Field(default=None, description="Active graph node")
    intent: IntentType = Field(default=IntentType.UNKNOWN)
    messages: List[Message] = Field(default_factory=list, description="Conversation transcript")
    
    # Domain slots & context
    context_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted domain entities (patient name, date, doctor, issue description, etc.)"
    )
    
    # Human-in-the-Loop state
    pending_action: Optional[ActionProposal] = Field(
        default=None,
        description="Active proposal awaiting human confirmation"
    )
    
    # Audit trail & node transition history
    transition_history: List[str] = Field(
        default_factory=list,
        description="Audit log of visited nodes"
    )
    
    # Final output synthesis
    final_output: Optional[str] = Field(default=None, description="Final user-facing response")
    is_completed: bool = Field(default=False, description="Flag indicating graph termination")

    def log_transition(self, node_name: str) -> None:
        """Record node traversal in audit history."""
        self.transition_history.append(f"{len(self.transition_history) + 1}: {node_name}")
        self.current_node = node_name

    def add_message(self, role: str, content: str, name: Optional[str] = None) -> None:
        """Append message to dialogue transcript."""
        self.messages.append(Message(role=role, content=content, name=name))

    def get_latest_user_message(self) -> str:
        """Retrieve content of the most recent user message."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to standard dictionary (Pydantic v2 model_dump)."""
        return self.model_dump()

    def get_history(self) -> List[str]:
        """Return transition audit history."""
        return list(self.transition_history)
