from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.quote import Quote
from core.ports.outbound.quote_repository import QuoteRepositoryPort


@dataclass
class ListQuotesResult:
    items: list[Quote]
    total: int
    offset: int
    limit: int


class ListQuotesUseCase:

    def __init__(self, quote_repo: QuoteRepositoryPort) -> None:
        self._repo = quote_repo

    async def execute(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ListQuotesResult:
        items, total = await self._repo.list_by_tenant(
            tenant_id,
            status=status,
            customer_id=customer_id,
            lead_id=lead_id,
            offset=offset,
            limit=limit,
        )
        return ListQuotesResult(items=items, total=total, offset=offset, limit=limit)
