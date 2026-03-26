"""
NullCalendarAdapter — no-op CalendarPort for agents without calendar integration.
"""

from __future__ import annotations

import logging
from typing import Optional

from core.ports.calendar_port import CalendarEvent, CalendarPort

logger = logging.getLogger(__name__)


class NullCalendarAdapter(CalendarPort):
    """Calendar adapter that silently ignores all operations."""

    async def create_event(self, event: CalendarEvent) -> Optional[str]:
        logger.debug("NullCalendarAdapter.create_event ignored: %s", event.title)
        return None

    async def list_upcoming_events(self, days_ahead: int = 7) -> list[CalendarEvent]:
        return []

    async def delete_event(self, event_id: str) -> bool:
        return True
