from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.quote import Quote, QuoteItem
from core.ports.outbound.premise_repository import PremiseRepositoryPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort


@dataclass(frozen=True)
class QuoteItemInput:
    description: str
    quantity: float
    unit_price: float
    discount: float = 0.0
    notes: str = ""


@dataclass(frozen=True)
class CreateQuoteRequest:
    tenant_id: UUID
    title: str
    customer_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    notes: str = ""
    valid_until: Optional[datetime] = None
    currency: str = "BRL"
    items: list[QuoteItemInput] = field(default_factory=list)
    premise_ids: list[UUID] = field(default_factory=list)
    sale_price: Optional[float] = None


class CreateQuoteUseCase:

    def __init__(
        self,
        quote_repo: QuoteRepositoryPort,
        premise_repo: PremiseRepositoryPort,
    ) -> None:
        self._quote_repo = quote_repo
        self._premise_repo = premise_repo

    async def execute(self, request: CreateQuoteRequest) -> Quote:
        quote = Quote.create(
            tenant_id=request.tenant_id,
            title=request.title,
            customer_id=request.customer_id,
            lead_id=request.lead_id,
            notes=request.notes,
            valid_until=request.valid_until,
            currency=request.currency,
        )

        for item_input in request.items:
            item = QuoteItem.create(
                quote_id=quote.id,
                description=item_input.description,
                quantity=item_input.quantity,
                unit_price=item_input.unit_price,
                discount=item_input.discount,
                notes=item_input.notes,
            )
            quote.items.append(item)

        if request.premise_ids:
            all_premises = await self._premise_repo.list_by_tenant(
                request.tenant_id, active_only=True
            )
            selected = [p for p in all_premises if p.id in request.premise_ids]
            quote.apply_premises(selected, sale_price_override=request.sale_price)

        await self._quote_repo.save(quote)
        return quote
