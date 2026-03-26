from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.customer import Customer
from core.ports.outbound.customer_repository import CustomerRepositoryPort


@dataclass(frozen=True)
class ListCustomersResult:
    items: list[Customer]
    total: int
    offset: int
    limit: int


class ListCustomersUseCase:

    def __init__(self, customer_repo: CustomerRepositoryPort) -> None:
        self._repo = customer_repo

    async def execute(
        self, tenant_id: UUID, offset: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> ListCustomersResult:
        items, total = await self._repo.list_by_tenant(tenant_id, offset, limit, search)
        return ListCustomersResult(items=items, total=total, offset=offset, limit=limit)
