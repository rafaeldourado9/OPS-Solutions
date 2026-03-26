from dataclasses import dataclass, field
from uuid import UUID

from core.domain.quote import Quote
from core.ports.outbound.premise_repository import PremiseRepositoryPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort


@dataclass(frozen=True)
class RecalculateQuoteRequest:
    tenant_id: UUID
    quote_id: UUID
    premise_ids: list[UUID] = field(default_factory=list)


class RecalculateQuoteUseCase:
    """Re-applies selected premises to a quote and persists the result."""

    def __init__(
        self,
        quote_repo: QuoteRepositoryPort,
        premise_repo: PremiseRepositoryPort,
    ) -> None:
        self._quote_repo = quote_repo
        self._premise_repo = premise_repo

    async def execute(self, request: RecalculateQuoteRequest) -> Quote:
        quote = await self._quote_repo.get_by_id(request.tenant_id, request.quote_id)
        if not quote:
            raise ValueError("Quote not found")

        all_premises = await self._premise_repo.list_by_tenant(
            request.tenant_id, active_only=True
        )
        selected = [p for p in all_premises if p.id in request.premise_ids]
        quote.apply_premises(selected)

        await self._quote_repo.update(quote)
        return quote
