from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.contract import Contract
from core.ports.outbound.contract_repository import ContractRepositoryPort


@dataclass
class ListContractsResult:
    items: list[Contract]
    total: int
    offset: int
    limit: int


class ListContractsUseCase:

    def __init__(self, contract_repo: ContractRepositoryPort) -> None:
        self._repo = contract_repo

    async def execute(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ListContractsResult:
        items, total = await self._repo.list_by_tenant(
            tenant_id, status=status, offset=offset, limit=limit
        )
        return ListContractsResult(items=items, total=total, offset=offset, limit=limit)
