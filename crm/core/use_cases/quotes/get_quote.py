from uuid import UUID

from core.domain.quote import Quote
from core.ports.outbound.quote_repository import QuoteRepositoryPort


class GetQuoteUseCase:

    def __init__(self, quote_repo: QuoteRepositoryPort) -> None:
        self._repo = quote_repo

    async def execute(self, tenant_id: UUID, quote_id: UUID) -> Quote:
        quote = await self._repo.get_by_id(tenant_id, quote_id)
        if not quote:
            raise ValueError("Quote not found")
        return quote
