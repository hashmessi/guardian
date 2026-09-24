"""Event injection scheduling, queue management, and modifier calculation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class InjectionEvent:
    """An injected anomaly, drift event, or operator intervention."""
    event_type: str
    start_cycle: int
    severity: float = 1.0
    duration: Optional[int] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def is_active_at(self, cycle: int) -> bool:
        """Check if this event is active at the specified cycle."""
        if cycle < self.start_cycle:
            return False
        if self.duration is not None and cycle >= self.start_cycle + self.duration:
            return False
        return True

    def get_cycle_offset(self, cycle: int) -> int:
        """Return how many cycles this event has been active."""
        return max(0, cycle - self.start_cycle + 1)


class EventQueue:
    """Queue of scheduled and active injection events."""

    def __init__(self):
        self.events: List[InjectionEvent] = []

    def add_event(self, event: InjectionEvent) -> None:
        """Add an event to the injection schedule."""
        self.events.append(event)

    def get_active_events(self, cycle: int) -> List[InjectionEvent]:
        """Return all events active at the specified cycle."""
        return [e for e in self.events if e.is_active_at(cycle)]

    def remove_event(self, event_type: str) -> None:
        """Remove events of a given type."""
        self.events = [e for e in self.events if e.event_type != event_type]

    def clear(self) -> None:
        """Clear all scheduled and active events."""
        self.events.clear()

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serialize events for inspection and audit logging."""
        return [
            {
                "event_type": e.event_type,
                "start_cycle": e.start_cycle,
                "severity": e.severity,
                "duration": e.duration,
                "params": e.params,
            }
            for e in self.events
        ]
