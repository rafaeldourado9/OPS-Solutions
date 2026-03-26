from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.lead import Lead, LeadStage
from core.ports.outbound.lead_repository import LeadRepositoryPort
from core.ports.outbound.message_broker_port import CRMEvent, MessageBrokerPort


@dataclass(frozen=True)
class MoveLeadStageRequest:
    tenant_id: UUID
    lead_id: UUID
    target_stage: str
    lost_reason: str = ""


class MoveLeadStageUseCase:

    def __init__(
        self,
        lead_repo: LeadRepositoryPort,
        broker: Optional[MessageBrokerPort] = None,
    ) -> None:
        self._repo = lead_repo
        self._broker = broker

    async def execute(self, request: MoveLeadStageRequest) -> Lead:
        lead = await self._repo.get_by_id(request.tenant_id, request.lead_id)
        if not lead:
            raise ValueError("Lead not found")

        try:
            target = LeadStage(request.target_stage)
        except ValueError:
            raise ValueError(f"Invalid stage: {request.target_stage}")

        previous_stage = lead.stage.value if hasattr(lead.stage, "value") else lead.stage
        lead.move_to(target, lost_reason=request.lost_reason)
        await self._repo.update(lead)

        if self._broker:
            await self._broker.publish(CRMEvent(
                event_type="crm.lead.stage_changed",
                tenant_id=str(request.tenant_id),
                payload={
                    "lead_id": str(lead.id),
                    "title": lead.title,
                    "previous_stage": previous_stage,
                    "new_stage": target.value,
                    "lost_reason": request.lost_reason,
                    "value": lead.value,
                },
            ))

        return lead
