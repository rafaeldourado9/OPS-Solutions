from uuid import UUID

from core.domain.premise import Premise
from core.ports.outbound.premise_repository import PremiseRepositoryPort


class ListPremisesUseCase:

    def __init__(self, premise_repo: PremiseRepositoryPort) -> None:
        self._repo = premise_repo

    async def execute(self, tenant_id: UUID, active_only: bool = True) -> list[Premise]:
        return await self._repo.list_by_tenant(tenant_id, active_only=active_only)
