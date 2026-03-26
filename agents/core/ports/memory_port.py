"""
MemoryPort — abstract interface for memory adapters (Qdrant, pgvector, …).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.domain.memory import Memory
from core.domain.message import Message


class MemoryPort(ABC):
    """Abstract port for semantic memory and RAG operations."""

    @abstractmethod
    async def save_message(self, message: Message) -> None:
        """
        Persist a message and its embedding in the vector store.

        Args:
            message: The Message domain entity to store.
        """
        ...

    @abstractmethod
    async def search_semantic(
        self,
        chat_id: str,
        query: str,
        k: int = 6,
    ) -> list[Memory]:
        """
        Return the K most semantically similar past messages for chat_id.

        Results are filtered strictly to the given chat_id so there is no
        context leakage between chats.

        Args:
            chat_id: The conversation to search within.
            query:   The query text (will be embedded internally).
            k:       Number of results to return.

        Returns:
            List of Memory objects sorted by similarity (highest first).
        """
        ...

    @abstractmethod
    async def get_recent(
        self,
        chat_id: str,
        n: int = 15,
        agent_id: str = "",
    ) -> list[Message]:
        """
        Return the N most recent messages for chat_id (oldest first).

        Args:
            chat_id:  The conversation to fetch.
            n:        Maximum number of messages to return.
            agent_id: When provided, restricts results to this agent only,
                      preventing context leakage between agents sharing a chat_id.

        Returns:
            Ordered list of Message objects.
        """
        ...

    @abstractmethod
    async def search_business_rules(
        self,
        query: str,
        k: int = 4,
        agent_id: str = "",
    ) -> list[str]:
        """
        Search the RAG collection for document chunks relevant to query.

        Args:
            query:    The user query or consolidated buffer text.
            k:        Number of chunks to return.
            agent_id: Used to select the correct RAG collection per agent.

        Returns:
            List of text chunks, sorted by relevance (highest first).
        """
        ...
