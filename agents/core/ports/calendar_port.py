"""
CalendarPort — abstract interface for calendar integrations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    title: str
    start: datetime
    end: datetime
    description: str = ""
    event_id: Optional[str] = None
    reminder_minutes: list[int] = field(default_factory=lambda: [2880, 60])  # 2 days + 1 hour


class CalendarPort(ABC):
    """Abstract port for calendar operations."""

    @abstractmethod
    async def create_event(self, event: CalendarEvent) -> Optional[str]:
        """
        Create a calendar event and return its ID.
        Returns None on failure.
        """
        ...

    @abstractmethod
    async def list_upcoming_events(self, days_ahead: int = 7) -> list[CalendarEvent]:
        """
        List events in the next N days.
        """
        ...

    @abstractmethod
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID. Returns True on success."""
        ...
