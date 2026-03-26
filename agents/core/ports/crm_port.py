"""
CRMPort — abstract interface for the CRM event bus.

The agent never knows a CRM exists; it simply calls push_event() after
meaningful actions.  The adapter decides what to do (HTTP POST, no-op, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CRMEvent:
    """
    A domain event to be forwarded to the external CRM.

    Attributes:
        event_type: A string identifier such as "new_contact",
                    "message_received", "agent_response_sent",
                    "conversation_closed".
        chat_id:    The conversation this event belongs to.
        agent_id:   The agent that generated the event.
        data:       Arbitrary payload — must be JSON-serialisable.
        timestamp:  UTC time the event was created.
    """

    event_type: str
    chat_id: str
    agent_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CRMPort(ABC):
    """Abstract port for CRM event publishing."""

    @abstractmethod
    async def push_event(self, event: CRMEvent) -> None:
        """
        Publish a CRM event.

        Implementations MUST be fire-and-forget — they must not raise
        exceptions to the caller under any circumstances.

        Args:
            event: The CRM event to publish.
        """
        ...
