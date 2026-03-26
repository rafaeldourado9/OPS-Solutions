from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class InboundAgentEvent:
    """Event received from the agents framework via CRMEventAdapter webhook."""

    event_type: str  # new_contact, message_received, agent_response_sent, conversation_closed
    chat_id: str
    agent_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
