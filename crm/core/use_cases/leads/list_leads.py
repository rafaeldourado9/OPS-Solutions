from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.lead import Lead
from core.ports.outbound.lead_repository import LeadRepositoryPort


@dataclass(frozen=True)
class ListLeadsResult:
    items: list[Lead]
    total: int
    offset: int
    limit: int


class ListLeadsUseCase:

    def __init__(self, lead_repo: LeadRepositoryPort) -> None:
        self._repo = lead_repo

    async def execute(
        self,
        tenant_id: UUID,
        stage: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ListLeadsResult:
        items, total = await self._repo.list_by_tenant(
            tenant_id, stage, assigned_to, search, offset, limit,
        )
        return ListLeadsResult(items=items, total=total, offset=offset, limit=limit)
