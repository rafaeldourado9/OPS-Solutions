from uuid import UUID

from core.ports.outbound.premise_repository import PremiseRepositoryPort


class DeletePremiseUseCase:

    def __init__(self, premise_repo: PremiseRepositoryPort) -> None:
        self._repo = premise_repo

    async def execute(self, tenant_id: UUID, premise_id: UUID) -> None:
        deleted = await self._repo.delete(tenant_id, premise_id)
        if not deleted:
            raise ValueError("Premise not found")
