"""
QdrantAdapter — vector store operations using Qdrant.

Handles:
  - Semantic search over past conversation messages (per chat_id)
  - RAG search over ingested business documents (per agent_id)
  - Embedding generation via Ollama nomic-embed-text

Collection naming:
  - Chat memory:    {agent_id}_chats  (one collection per agent)
  - Business rules: {agent_id}_rules  (populated by ingest script)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
    FilterSelector,
)

from adapters.outbound.llm.ollama_adapter import get_embedding
from core.domain.memory import Memory
from core.domain.message import Message

logger = logging.getLogger(__name__)

# nomic-embed-text produces 768-dimensional vectors
_EMBEDDING_DIM = 768


class QdrantAdapter:
    """
    Qdrant operations for semantic search.

    This class is used by HybridMemoryAdapter — it does NOT implement
    MemoryPort directly (save and get_recent are delegated to Postgres).

    Args:
        chat_collection:  Qdrant collection name for conversation memory.
        rules_collection: Qdrant collection name for business rules (RAG).
        embedding_model:  Ollama model used for embedding generation.
        qdrant_url:       Qdrant server URL; falls back to QDRANT_URL env var.
        qdrant_api_key:   Optional API key for hosted Qdrant.
    """

    def __init__(
        self,
        chat_collection: str,
        rules_collection: str,
        embedding_model: str = "nomic-embed-text",
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
    ) -> None:
        url = qdrant_url or os.environ.get("QDRANT_URL", "http://localhost:6333")
        api_key = qdrant_api_key or os.environ.get("QDRANT_API_KEY") or None
        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._chat_collection = chat_collection
        self._rules_collection = rules_collection
        self._embedding_model = embedding_model

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def ensure_collections(self) -> None:
        """
        Create chat and rules collections if they don't exist yet.
        Safe to call multiple times (idempotent).
        """
        for name in (self._chat_collection, self._rules_collection):
            exists = await self._collection_exists(name)
            if not exists:
                await self._client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=_EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )
                # Create payload index on chat_id / agent_id for fast filtering
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="chat_id",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="agent_id",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                logger.info("Created Qdrant collection: %s", name)

    async def _collection_exists(self, name: str) -> bool:
        try:
            await self._client.get_collection(name)
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.close()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def save_message_vector(self, message: Message) -> None:
        """Embed a message and upsert it into the chat collection."""
        try:
            vector = await get_embedding(
                text=message.content,
                model=self._embedding_model,
            )
        except Exception:
            logger.exception(
                "Embedding failed for message %s — skipping Qdrant upsert", message.id
            )
            return

        payload = {
            "chat_id": message.chat_id,
            "agent_id": message.agent_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
        }

        try:
            await self._client.upsert(
                collection_name=self._chat_collection,
                points=[PointStruct(id=message.id, vector=vector, payload=payload)],
            )
        except Exception:
            logger.exception(
                "Qdrant upsert failed for message %s in collection %s",
                message.id,
                self._chat_collection,
            )

    # ------------------------------------------------------------------
    # Semantic search — conversations
    # ------------------------------------------------------------------

    async def search_semantic(
        self,
        chat_id: str,
        query: str,
        k: int = 6,
    ) -> list[Memory]:
        """Return K semantically similar past messages for the given chat_id."""
        try:
            vector = await get_embedding(text=query, model=self._embedding_model)
        except Exception:
            logger.exception("Embedding failed for semantic search query")
            return []

        chat_filter = Filter(
            must=[FieldCondition(key="chat_id", match=MatchValue(value=chat_id))]
        )

        try:
            results = await self._client.search(
                collection_name=self._chat_collection,
                query_vector=vector,
                query_filter=chat_filter,
                limit=k,
                with_payload=True,
            )
        except Exception:
            logger.exception(
                "Qdrant search failed for chat_id=%s collection=%s",
                chat_id,
                self._chat_collection,
            )
            return []

        memories: list[Memory] = []
        for hit in results:
            payload = hit.payload or {}
            memories.append(
                Memory(
                    id=str(hit.id),
                    chat_id=payload.get("chat_id", chat_id),
                    content=payload.get("content", ""),
                    score=hit.score,
                )
            )
        return memories

    # ------------------------------------------------------------------
    # RAG search — business rules
    # ------------------------------------------------------------------

    async def search_business_rules(
        self,
        query: str,
        k: int = 4,
        agent_id: str = "",
    ) -> list[str]:
        """Return K relevant text chunks from the RAG collection."""
        try:
            vector = await get_embedding(text=query, model=self._embedding_model)
        except Exception:
            logger.exception("Embedding failed for business rules query")
            return []

        search_filter: Optional[Filter] = None
        if agent_id:
            search_filter = Filter(
                must=[FieldCondition(key="agent_id", match=MatchValue(value=agent_id))]
            )

        try:
            results = await self._client.search(
                collection_name=self._rules_collection,
                query_vector=vector,
                query_filter=search_filter,
                limit=k,
                with_payload=True,
            )
        except Exception:
            logger.exception(
                "Qdrant search failed for rules collection=%s agent_id=%s",
                self._rules_collection,
                agent_id,
            )
            return []

        chunks: list[str] = []
        for hit in results:
            payload = hit.payload or {}
            text = payload.get("content") or payload.get("text") or ""
            if text:
                chunks.append(text)
        return chunks

    # ------------------------------------------------------------------
    # Upsert for RAG ingestion (used by ingest script)
    # ------------------------------------------------------------------

    async def upsert_document_chunk(
        self,
        point_id: str,
        text: str,
        agent_id: str,
        source: str = "",
        chunk_index: int = 0,
    ) -> None:
        """
        Embed and upsert a document chunk into the RAG collection.
        Called by IngestDocumentsUseCase / scripts/ingest.py.
        """
        try:
            vector = await get_embedding(text=text, model=self._embedding_model)
        except Exception:
            logger.exception("Embedding failed for chunk from source=%s", source)
            return

        payload = {
            "agent_id": agent_id,
            "content": text,
            "source": source,
            "chunk_index": chunk_index,
        }

        await self._client.upsert(
            collection_name=self._rules_collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    # ------------------------------------------------------------------
    # RAG document management — list and delete by source
    # ------------------------------------------------------------------

    async def list_document_sources(self, agent_id: str) -> list[dict]:
        """
        Return a list of unique document sources in the rules collection
        for the given agent_id, with the chunk count for each.

        Returns:
            List of dicts: [{"source": str, "chunks": int}, ...]
        """
        agent_filter = Filter(
            must=[FieldCondition(key="agent_id", match=MatchValue(value=agent_id))]
        )
        try:
            results, _ = await self._client.scroll(
                collection_name=self._rules_collection,
                scroll_filter=agent_filter,
                limit=10000,
                with_payload=True,
                with_vectors=False,
            )
        except Exception:
            logger.exception(
                "Qdrant scroll failed for rules collection=%s agent_id=%s",
                self._rules_collection,
                agent_id,
            )
            return []

        # Count chunks per source
        counts: dict[str, int] = {}
        for point in results:
            payload = point.payload or {}
            source = payload.get("source", "(sem nome)")
            counts[source] = counts.get(source, 0) + 1

        return [
            {"source": src, "chunks": cnt}
            for src, cnt in sorted(counts.items())
        ]

    async def delete_by_source(self, agent_id: str, source_name: str) -> int:
        """
        Delete all document chunks from the rules collection that match
        both agent_id and source_name.

        Returns:
            Number of points deleted (approximate — Qdrant does not return count).
        """
        delete_filter = Filter(
            must=[
                FieldCondition(key="agent_id", match=MatchValue(value=agent_id)),
                FieldCondition(key="source", match=MatchValue(value=source_name)),
            ]
        )
        try:
            await self._client.delete(
                collection_name=self._rules_collection,
                points_selector=FilterSelector(filter=delete_filter),
            )
            logger.info(
                "Deleted source='%s' from collection=%s agent_id=%s",
                source_name,
                self._rules_collection,
                agent_id,
            )
            return 0  # Qdrant delete does not return count
        except Exception:
            logger.exception(
                "Qdrant delete failed for source='%s' collection=%s agent_id=%s",
                source_name,
                self._rules_collection,
                agent_id,
            )
            return 0
