from uuid import UUID

from core.ports.outbound.contract_template_repository import ContractTemplateRepositoryPort
from core.ports.outbound.storage_port import StoragePort


class DeleteContractTemplateUseCase:

    def __init__(
        self,
        template_repo: ContractTemplateRepositoryPort,
        storage: StoragePort,
    ) -> None:
        self._repo = template_repo
        self._storage = storage

    async def execute(self, tenant_id: UUID, template_id: UUID) -> bool:
        template = await self._repo.get_by_id(tenant_id, template_id)
        if not template:
            return False

        deleted = await self._repo.delete(tenant_id, template_id)
        if deleted and template.file_key:
            try:
                await self._storage.delete(template.file_key)
            except Exception:
                pass
        return deleted
