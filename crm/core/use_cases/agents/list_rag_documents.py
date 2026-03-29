from uuid import UUID

from core.domain.rag_document import RagDocument
from core.ports.outbound.agent_config_port import AgentConfigPort
from core.ports.outbound.rag_document_port import RagDocumentPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


class ListRagDocumentsUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        config_port: AgentConfigPort,
        rag_port: RagDocumentPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._config_port = config_port
        self._rag_port = rag_port

    async def execute(self, tenant_id: UUID, agent_id: str | None = None) -> list[RagDocument]:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        target = agent_id or tenant.agent_id
        config = self._config_port.read(target)
        collection = config.get("memory", {}).get(
            "qdrant_rag_collection", f"{target}_rules"
        )
        return await self._rag_port.list_documents(collection)
