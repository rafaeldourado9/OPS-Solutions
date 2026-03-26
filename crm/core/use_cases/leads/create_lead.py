from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.lead import Lead
from core.ports.outbound.lead_repository import LeadRepositoryPort


@dataclass(frozen=True)
class CreateLeadRequest:
    tenant_id: UUID
    title: str
    customer_id: Optional[UUID] = None
    value: float = 0.0
    source: str = "manual"
    assigned_to: Optional[UUID] = None
    notes: str = ""
    expected_close_date: Optional[datetime] = None
    tags: list[str] | None = None


class CreateLeadUseCase:

    def __init__(self, lead_repo: LeadRepositoryPort) -> None:
        self._repo = lead_repo

    async def execute(self, request: CreateLeadRequest) -> Lead:
        lead = Lead.create(
            tenant_id=request.tenant_id,
            title=request.title,
            customer_id=request.customer_id,
            value=request.value,
            source=request.source,
            assigned_to=request.assigned_to,
            notes=request.notes,
            expected_close_date=request.expected_close_date,
            tags=request.tags,
        )
        await self._repo.save(lead)
        return lead
