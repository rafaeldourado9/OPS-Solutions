from dataclasses import dataclass
from uuid import UUID

from core.ports.outbound.agent_config_port import AgentConfigPort
from core.ports.outbound.rag_document_port import RagDocumentPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


@dataclass(frozen=True)
class DeleteRagDocumentRequest:
    tenant_id: UUID
    doc_name: str


class DeleteRagDocumentUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        config_port: AgentConfigPort,
        rag_port: RagDocumentPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._config_port = config_port
        self._rag_port = rag_port

    async def execute(self, request: DeleteRagDocumentRequest) -> int:
        tenant = await self._tenant_repo.get_by_id(request.tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        config = self._config_port.read(tenant.agent_id)
        collection = config.get("memory", {}).get(
            "qdrant_rag_collection", f"{tenant.agent_id}_rules"
        )

        deleted = await self._rag_port.delete_document(collection, request.doc_name)
        if deleted == 0:
            raise ValueError(f"Document '{request.doc_name}' not found in RAG collection")
        return deleted
