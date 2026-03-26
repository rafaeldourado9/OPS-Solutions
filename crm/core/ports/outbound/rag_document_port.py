from abc import ABC, abstractmethod

from core.domain.rag_document import RagDocument


class RagDocumentPort(ABC):

    @abstractmethod
    async def list_documents(self, collection: str) -> list[RagDocument]:
        """Lists all unique documents ingested into the given Qdrant collection."""
        ...

    @abstractmethod
    async def ingest_document(
        self, collection: str, name: str, text_chunks: list[str]
    ) -> int:
        """Ingests text chunks into the collection under the given document name.
        Returns the number of chunks upserted."""
        ...

    @abstractmethod
    async def delete_document(self, collection: str, name: str) -> int:
        """Deletes all points for the given document name. Returns count deleted."""
        ...
