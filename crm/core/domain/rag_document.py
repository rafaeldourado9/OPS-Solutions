from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RagDocument:
    """Represents a document ingested into the RAG vector store (Qdrant)."""
    name: str
    collection: str
    chunk_count: int
    ingested_at: Optional[datetime] = None
