"""
Domain entities for memory and context windows.

No infrastructure imports — pure domain models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from core.domain.message import Message


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


class Memory(BaseModel):
    """
    A single piece of semantic memory stored in the vector database.

    Each Memory corresponds to one embedded message or document chunk.

    Attributes:
        id:         Unique identifier — also used as the Qdrant point ID.
        chat_id:    Owner chat; used for payload filtering in Qdrant.
        content:    The text that was embedded.
        embedding:  Vector produced by the embedding model.  May be empty
                    when the object is constructed before embedding.
        score:      Similarity score returned by Qdrant (0–1), set after search.
        created_at: UTC creation time.
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(default_factory=lambda: str(uuid4()))
    chat_id: str
    content: str
    embedding: list[float] = Field(default_factory=list)
    score: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# ContextWindow
# ---------------------------------------------------------------------------


class ContextWindow(BaseModel):
    """
    The assembled context that is passed to the LLM for a single inference.

    Attributes:
        recent_messages:   The N most recent messages from the conversation
                           (pulled from PostgreSQL or Qdrant).
        semantic_memories: The K most semantically similar past messages
                           (pulled from Qdrant by vector similarity).
        business_rules:    Relevant chunks from the company's documents
                           (pulled from the RAG collection in Qdrant).
    """

    recent_messages: list[Message] = Field(default_factory=list)
    semantic_memories: list[Memory] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)

    def has_business_context(self) -> bool:
        """Return True if at least one business rule chunk is available."""
        return len(self.business_rules) > 0

    def format_business_rules(self) -> str:
        """Return business rules as a numbered string block for the system prompt."""
        if not self.business_rules:
            return ""
        lines = ["Contexto relevante dos documentos da empresa:"]
        for i, rule in enumerate(self.business_rules, start=1):
            lines.append(f"{i}. {rule}")
        return "\n".join(lines)

    def format_semantic_memories(self) -> str:
        """Return semantic memories as a string block for the system prompt."""
        if not self.semantic_memories:
            return ""
        lines = ["Memórias semânticas relevantes desta conversa:"]
        for mem in self.semantic_memories:
            lines.append(f"- {mem.content}")
        return "\n".join(lines)
