"""
BuildContextUseCase — assembles the hybrid context window for a single inference.

Combines:
  1. Recent messages    — always included (immediate conversational context)
  2. Semantic memories  — most relevant past messages via vector similarity
  3. Business rules     — most relevant RAG chunks from company documents
"""

from __future__ import annotations

import logging

from core.domain.memory import ContextWindow
from core.ports.memory_port import MemoryPort
from infrastructure.config_loader import BusinessConfig

logger = logging.getLogger(__name__)

# Indicates the query is casual and doesn't need semantic/RAG search
_SKIP_SEARCH_FLAG = "_casual"


class BuildContextUseCase:
    """
    Builds a ContextWindow for use by ProcessMessageUseCase.

    Args:
        memory: The MemoryPort implementation.
        config: The BusinessConfig for the active agent.
    """

    def __init__(self, memory: MemoryPort, config: BusinessConfig) -> None:
        self._memory = memory
        self._config = config

    async def build(
        self,
        chat_id: str,
        query: str,
        agent_id: str,
        skip_search: bool = False,
    ) -> ContextWindow:
        """
        Assemble and return a ContextWindow.

        Args:
            chat_id:    The conversation identifier.
            query:      The consolidated user query (all buffered messages joined).
            agent_id:   The active agent identifier (for RAG collection selection).
            skip_search: If True, skip semantic and RAG search (for casual messages).

        Returns:
            A populated ContextWindow.
        """
        mem_cfg = self._config.memory

        # 1. Fetch recent messages (always included for conversational coherence)
        # agent_id is passed so messages from other agents on the same chat_id
        # are never included — prevents context leakage in multi-agent setups.
        try:
            recent = await self._memory.get_recent(
                chat_id=chat_id,
                n=mem_cfg.max_recent_messages,
                agent_id=agent_id,
            )
        except Exception:
            logger.exception(
                "get_recent failed for chat_id=%s; proceeding without history.",
                chat_id,
            )
            recent = []

        # For casual messages (greetings, farewells, acknowledgements),
        # skip semantic search and RAG — they only add noise and cause hallucination.
        if skip_search:
            logger.debug(
                "Skipping semantic/RAG search for casual message in chat_id=%s",
                chat_id,
            )
            return ContextWindow(
                recent_messages=recent,
                semantic_memories=[],
                business_rules=[],
            )

        # 2. Fetch semantically similar past messages
        semantic = []
        if query:
            try:
                semantic = await self._memory.search_semantic(
                    chat_id=chat_id,
                    query=query,
                    k=mem_cfg.semantic_k,
                )
            except Exception:
                logger.exception(
                    "Semantic search failed for chat_id=%s; proceeding without it.",
                    chat_id,
                )

        # 3. Fetch relevant business rules from RAG collection
        business_rules: list[str] = []
        if query:
            try:
                business_rules = await self._memory.search_business_rules(
                    query=query,
                    k=4,
                    agent_id=agent_id,
                )
            except Exception:
                logger.exception(
                    "Business rules search failed for agent_id=%s; proceeding without it.",
                    agent_id,
                )

        context = ContextWindow(
            recent_messages=recent,
            semantic_memories=semantic,
            business_rules=business_rules,
        )

        logger.debug(
            "Context built for chat_id=%s: recent=%d semantic=%d rules=%d",
            chat_id,
            len(recent),
            len(semantic),
            len(business_rules),
        )

        return context
