from uuid import UUID

from core.domain.contract_template import ContractTemplate
from core.ports.outbound.contract_template_repository import ContractTemplateRepositoryPort


class ListContractTemplatesUseCase:

    def __init__(self, template_repo: ContractTemplateRepositoryPort) -> None:
        self._repo = template_repo

    async def execute(self, tenant_id: UUID) -> list[ContractTemplate]:
        return await self._repo.list_by_tenant(tenant_id)
