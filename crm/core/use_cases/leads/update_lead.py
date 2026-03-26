from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.lead import Lead
from core.ports.outbound.lead_repository import LeadRepositoryPort


@dataclass(frozen=True)
class UpdateLeadRequest:
    tenant_id: UUID
    lead_id: UUID
    title: Optional[str] = None
    customer_id: Optional[UUID] = None
    value: Optional[float] = None
    source: Optional[str] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    tags: Optional[list[str]] = None


class UpdateLeadUseCase:

    def __init__(self, lead_repo: LeadRepositoryPort) -> None:
        self._repo = lead_repo

    async def execute(self, request: UpdateLeadRequest) -> Lead:
        lead = await self._repo.get_by_id(request.tenant_id, request.lead_id)
        if not lead:
            raise ValueError("Lead not found")

        if request.title is not None:
            lead.title = request.title
        if request.customer_id is not None:
            lead.customer_id = request.customer_id
        if request.value is not None:
            lead.value = request.value
        if request.source is not None:
            lead.source = request.source
        if request.assigned_to is not None:
            lead.assigned_to = request.assigned_to
        if request.notes is not None:
            lead.notes = request.notes
        if request.expected_close_date is not None:
            lead.expected_close_date = request.expected_close_date
        if request.tags is not None:
            lead.tags = request.tags

        lead.updated_at = datetime.utcnow()
        await self._repo.update(lead)
        return lead
