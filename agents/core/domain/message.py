"""
Domain entities for messages and conversations.

These are pure Python dataclasses / Pydantic models with zero infrastructure
dependencies.  They are the lingua franca of the core layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Role literal
# ---------------------------------------------------------------------------

Role = Literal["user", "assistant", "system"]


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------


class Message(BaseModel):
    """
    A single message in a conversation.

    Attributes:
        id:         Unique message identifier (UUID4 by default).
        chat_id:    Identifies the WhatsApp chat (phone number or group JID).
        agent_id:   Which agent configuration handled this message.
        role:       "user" | "assistant" | "system".
        content:    Text content of the message.
        media_type: Optional MIME-like tag — "audio", "image", "video",
                    "document", or None for plain text.
        timestamp:  UTC creation time.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    chat_id: str
    agent_id: str
    role: Role
    content: str
    media_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_llm_dict(self) -> dict[str, str]:
        """Return the message in the format expected by most LLM APIs."""
        return {"role": self.role, "content": self.content}


# ---------------------------------------------------------------------------
# MediaMessage
# ---------------------------------------------------------------------------


class MediaMessage(Message):
    """
    A message that carries media in addition to (or instead of) text.

    The ``content`` field holds the human-readable transcription or
    description produced by the media pipeline so that the LLM always
    receives plain text.

    Attributes:
        media_url:  Remote URL where the raw media can be fetched (e.g. WAHA).
        media_data: Raw bytes of the media file once downloaded.
    """

    model_config = ConfigDict(frozen=False)  # media_data may be set after construction

    media_url: Optional[str] = None
    media_data: Optional[bytes] = None


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------


class Conversation(BaseModel):
    """
    An ordered collection of messages belonging to a single chat.

    Attributes:
        chat_id:  Identifies the WhatsApp chat.
        agent_id: Which agent is handling this conversation.
        messages: Ordered list of messages (oldest first).
    """

    chat_id: str
    agent_id: str
    messages: list[Message] = Field(default_factory=list)

    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def last_user_message(self) -> Optional[Message]:
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None

    def to_llm_messages(self) -> list[dict[str, str]]:
        """Convert to the list-of-dicts format expected by most LLM APIs."""
        return [m.to_llm_dict() for m in self.messages if m.role != "system"]
