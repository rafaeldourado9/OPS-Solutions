from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.quote import Quote, QuoteStatus
from core.ports.outbound.message_broker_port import CRMEvent, MessageBrokerPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort


@dataclass(frozen=True)
class UpdateQuoteStatusRequest:
    tenant_id: UUID
    quote_id: UUID
    status: str


class UpdateQuoteStatusUseCase:

    def __init__(
        self,
        quote_repo: QuoteRepositoryPort,
        broker: Optional[MessageBrokerPort] = None,
    ) -> None:
        self._repo = quote_repo
        self._broker = broker

    async def execute(self, request: UpdateQuoteStatusRequest) -> Quote:
        quote = await self._repo.get_by_id(request.tenant_id, request.quote_id)
        if not quote:
            raise ValueError("Quote not found")

        target = QuoteStatus(request.status)
        if not quote.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from '{quote.status.value}' to '{target.value}'"
            )

        previous_status = quote.status.value
        quote.status = target
        quote.updated_at = datetime.utcnow()
        await self._repo.update(quote)

        if self._broker:
            await self._broker.publish(CRMEvent(
                event_type="crm.quote.status_changed",
                tenant_id=str(request.tenant_id),
                payload={
                    "quote_id": str(quote.id),
                    "title": quote.title,
                    "previous_status": previous_status,
                    "new_status": target.value,
                    "total": quote.total,
                    "customer_id": str(quote.customer_id) if quote.customer_id else None,
                    "lead_id": str(quote.lead_id) if quote.lead_id else None,
                },
            ))

        return quote
