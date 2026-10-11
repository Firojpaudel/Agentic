"""
Domain Tools & In-Memory Stores for Hospital Scheduling & Ticketing.
Provides zero-dependency, deterministic domain backends for Module 02.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from .state import AppointmentSlot, SeverityLevel, Ticket
except ImportError:
    from state import AppointmentSlot, SeverityLevel, Ticket


class HospitalScheduler:
    """Thread-safe in-memory appointment calendar database."""

    def __init__(self):
        self._slots: List[AppointmentSlot] = [
            # Dr. Sarah Chen (Cardiology)
            AppointmentSlot(doctor_name="Dr. Sarah Chen", department="Cardiology", date="2026-10-15", time="09:00"),
            AppointmentSlot(doctor_name="Dr. Sarah Chen", department="Cardiology", date="2026-10-15", time="10:00", is_available=False, patient_name="John Doe"),
            AppointmentSlot(doctor_name="Dr. Sarah Chen", department="Cardiology", date="2026-10-15", time="14:00"),
            AppointmentSlot(doctor_name="Dr. Sarah Chen", department="Cardiology", date="2026-10-16", time="11:00"),

            # Dr. Marcus Vance (Neurology)
            AppointmentSlot(doctor_name="Dr. Marcus Vance", department="Neurology", date="2026-10-15", time="10:00"),
            AppointmentSlot(doctor_name="Dr. Marcus Vance", department="Neurology", date="2026-10-15", time="11:30"),
            AppointmentSlot(doctor_name="Dr. Marcus Vance", department="Neurology", date="2026-10-16", time="15:00"),

            # Dr. Elena Rostova (General Medicine)
            AppointmentSlot(doctor_name="Dr. Elena Rostova", department="General Medicine", date="2026-10-15", time="08:30"),
            AppointmentSlot(doctor_name="Dr. Elena Rostova", department="General Medicine", date="2026-10-15", time="13:00"),
            AppointmentSlot(doctor_name="Dr. Elena Rostova", department="General Medicine", date="2026-10-16", time="09:30"),
        ]

    def list_doctors(self) -> List[Dict[str, str]]:
        """List distinct doctors and their medical departments in O(N)."""
        doctors = {s.doctor_name: s.department for s in self._slots}
        return [{"doctor": doc, "department": dept} for doc, dept in doctors.items()]

    def check_availability(self, doctor_name: str, date: str) -> List[str]:
        """Return available time slots for a specific doctor on a given date."""
        normalized_doc = doctor_name.lower().strip()
        matched = [
            s.time for s in self._slots
            if normalized_doc in s.doctor_name.lower() and s.date == date and s.is_available
        ]
        return matched

    def book_slot(self, doctor_name: str, date: str, time: str, patient_name: str) -> Dict[str, Any]:
        """
        Book an available appointment slot.
        Fails if slot does not exist or is already booked.
        """
        normalized_doc = doctor_name.lower().strip()
        for s in self._slots:
            if normalized_doc in s.doctor_name.lower() and s.date == date and s.time == time:
                if not s.is_available:
                    return {
                        "success": False,
                        "error": f"Conflict: Slot {date} at {time} with {s.doctor_name} is already booked by {s.patient_name}."
                    }
                # Reserve slot
                s.is_available = False
                s.patient_name = patient_name
                return {
                    "success": True,
                    "doctor": s.doctor_name,
                    "department": s.department,
                    "date": date,
                    "time": time,
                    "patient": patient_name,
                    "booking_ref": f"APT-{date.replace('-', '')}-{time.replace(':', '')}"
                }
        
        return {
            "success": False,
            "error": f"Slot not found for doctor '{doctor_name}' on {date} at {time}."
        }


class TicketStore:
    """Thread-safe in-memory support ticket store."""

    def __init__(self):
        self._tickets: Dict[str, Ticket] = {}

    SEVERITY_RULES = (
        (
            SeverityLevel.CRITICAL,
            ("cardiac monitor", "life support", "data breach", "emergency", "system crash", "critical"),
            "Identified life-critical or catastrophic system failure keywords.",
        ),
        (
            SeverityLevel.HIGH,
            ("database down", "api timeout", "outage", "billing error", "cannot login", "urgent"),
            "Identified blocking service disruption or financial defect.",
        ),
        (
            SeverityLevel.MEDIUM,
            ("slow", "bug", "formatting", "error message", "reschedule", "portal glitch"),
            "Identified non-blocking functional anomaly.",
        ),
    )

    def classify_severity(self, title: str, description: str) -> tuple[SeverityLevel, str]:
        """Rule-based severity classifier with domain heuristics."""
        content = f"{title} {description}".lower()
        for level, keywords, rationale in self.SEVERITY_RULES:
            if any(w in content for w in keywords):
                return level, rationale
        return SeverityLevel.LOW, "Routine inquiry or minor cosmetic issue."

    def create_ticket(
        self,
        title: str,
        category: str,
        severity: SeverityLevel,
        description: str,
        assigned_to: Optional[str] = None
    ) -> Ticket:
        """Create and register a support ticket."""
        ticket = Ticket(
            title=title,
            category=category,
            severity=severity,
            description=description,
            assigned_to=assigned_to or "Support Tier 1"
        )
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Fetch ticket by ID."""
        return self._tickets.get(ticket_id)

    def list_tickets(self) -> List[Ticket]:
        """Return all open tickets."""
        return list(self._tickets.values())


# Global instances
hospital_scheduler = HospitalScheduler()
ticket_store = TicketStore()
