from uuid import UUID

from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.ports.outbound.storage_port import StoragePort


class DeleteQuoteTemplateUseCase:

    def __init__(
        self,
        template_repo: QuoteTemplateRepositoryPort,
        storage: StoragePort,
    ) -> None:
        self._repo = template_repo
        self._storage = storage

    async def execute(self, tenant_id: UUID, template_id: UUID) -> None:
        template = await self._repo.get_by_id(tenant_id, template_id)
        if not template:
            raise ValueError("Template not found")

        await self._storage.delete(template.file_key)
        await self._repo.delete(tenant_id, template_id)
