from uuid import UUID

from core.domain.lead import Lead
from core.ports.outbound.lead_repository import LeadRepositoryPort


class GetLeadUseCase:

    def __init__(self, lead_repo: LeadRepositoryPort) -> None:
        self._repo = lead_repo

    async def execute(self, tenant_id: UUID, lead_id: UUID) -> Lead:
        lead = await self._repo.get_by_id(tenant_id, lead_id)
        if not lead:
            raise ValueError("Lead not found")
        return lead
