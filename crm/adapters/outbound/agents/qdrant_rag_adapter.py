"""
QdrantRagAdapter — manages RAG documents via Qdrant REST API + Gemini embeddings.

Uses httpx directly (no qdrant-client dependency) for clean separation.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import structlog

from core.domain.rag_document import RagDocument
from core.ports.outbound.rag_document_port import RagDocumentPort
from infrastructure.config import settings

logger = structlog.get_logger()

_VECTOR_SIZE = 3072  # gemini-embedding-001
_GEMINI_EMBED_MODEL = "models/gemini-embedding-001"
_GEMINI_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-embedding-001:embedContent?key={key}"
)


def _read_gemini_key() -> str:
    """Read Gemini API key from shared file or fall back to GEMINI_API_KEY env var."""
    agents_dir = os.environ.get("AGENTS_DIR", "/app/shared-agents")
    key_file = Path(agents_dir) / ".gemini_key"
    try:
        key = key_file.read_text().strip()
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")


class QdrantRagAdapter(RagDocumentPort):

    def __init__(self, qdrant_url: str | None = None) -> None:
        self._qdrant = (qdrant_url or settings.qdrant_url).rstrip("/")
        self._client = httpx.AsyncClient(timeout=60.0)

    async def _get_embedding(self, text: str) -> list[float]:
        api_key = _read_gemini_key()
        if not api_key:
            raise ValueError(
                "Gemini API key not configured. "
                "Go to Settings → Integrations and save your Gemini key."
            )
        resp = await self._client.post(
            _GEMINI_EMBED_URL.format(key=api_key),
            json={
                "model": _GEMINI_EMBED_MODEL,
                "content": {"parts": [{"text": text}]},
            },
        )
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]

    async def _ensure_collection(self, collection: str) -> None:
        check = await self._client.get(f"{self._qdrant}/collections/{collection}")
        if check.status_code == 200:
            # Verify vector size matches — recreate if different (e.g. migrated from 768)
            existing_size = (
                check.json()
                .get("result", {})
                .get("config", {})
                .get("params", {})
                .get("vectors", {})
                .get("size")
            )
            if existing_size == _VECTOR_SIZE:
                return
            # Wrong dimensions — delete and recreate (only safe when collection is empty)
            count_resp = await self._client.post(
                f"{self._qdrant}/collections/{collection}/points/count",
                json={},
            )
            count = count_resp.json().get("result", {}).get("count", 1) if count_resp.status_code == 200 else 1
            if count > 0:
                logger.warning(
                    "rag_collection_dim_mismatch",
                    collection=collection,
                    existing=existing_size,
                    expected=_VECTOR_SIZE,
                    points=count,
                )
                return  # Don't touch a collection with existing data
            await self._client.delete(f"{self._qdrant}/collections/{collection}")

        resp = await self._client.put(
            f"{self._qdrant}/collections/{collection}",
            json={"vectors": {"size": _VECTOR_SIZE, "distance": "Cosine"}},
        )
        # 200 = created, 409 = already exists (concurrent creation) — both are fine
        if resp.status_code not in (200, 409):
            resp.raise_for_status()

    async def list_documents(self, collection: str) -> list[RagDocument]:
        # Scroll through all points and aggregate unique doc names
        check = await self._client.get(f"{self._qdrant}/collections/{collection}")
        if check.status_code == 404:
            return []

        resp = await self._client.post(
            f"{self._qdrant}/collections/{collection}/points/scroll",
            json={"limit": 10000, "with_payload": True, "with_vector": False},
        )
        if resp.status_code != 200:
            return []

        points = resp.json().get("result", {}).get("points", [])
        docs: dict[str, dict[str, Any]] = {}
        for p in points:
            payload = p.get("payload", {})
            name = payload.get("doc_name", "unknown")
            if name not in docs:
                docs[name] = {"count": 0, "ingested_at": payload.get("ingested_at")}
            docs[name]["count"] += 1

        return [
            RagDocument(
                name=name,
                collection=collection,
                chunk_count=info["count"],
                ingested_at=datetime.fromisoformat(info["ingested_at"])
                if info.get("ingested_at")
                else None,
            )
            for name, info in sorted(docs.items())
        ]

    async def ingest_document(
        self, collection: str, name: str, text_chunks: list[str], agent_id: str = "",
    ) -> int:
        await self._ensure_collection(collection)

        # Derive agent_id from collection name if not provided (e.g. "mab_rules" → "mab")
        effective_agent_id = agent_id or (
            collection.removesuffix("_rules") if collection.endswith("_rules") else ""
        )

        ingested_at = datetime.now(timezone.utc).isoformat()
        points = []

        for chunk in text_chunks:
            try:
                vector = await self._get_embedding(chunk)
            except ValueError:
                # Configuration errors (missing key) must propagate immediately
                raise
            except Exception as e:
                logger.warning("embedding_failed", chunk_preview=chunk[:50], error=str(e))
                continue

            payload: dict = {
                "doc_name": name,
                "text": chunk,
                "ingested_at": ingested_at,
            }
            if effective_agent_id:
                payload["agent_id"] = effective_agent_id

            points.append({
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": payload,
            })

        if not points:
            return 0

        resp = await self._client.put(
            f"{self._qdrant}/collections/{collection}/points",
            json={"points": points},
        )
        resp.raise_for_status()
        return len(points)

    async def delete_document(self, collection: str, name: str) -> int:
        check = await self._client.get(f"{self._qdrant}/collections/{collection}")
        if check.status_code == 404:
            return 0

        # Count existing points first
        docs = await self.list_documents(collection)
        existing = next((d for d in docs if d.name == name), None)
        if not existing:
            return 0

        resp = await self._client.post(
            f"{self._qdrant}/collections/{collection}/points/delete",
            json={
                "filter": {
                    "must": [{"key": "doc_name", "match": {"value": name}}]
                }
            },
        )
        resp.raise_for_status()
        return existing.chunk_count

    async def close(self) -> None:
        await self._client.aclose()
