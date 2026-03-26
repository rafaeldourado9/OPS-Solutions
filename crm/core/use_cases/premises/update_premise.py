from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.premise import PremiseType
from core.ports.outbound.premise_repository import PremiseRepositoryPort


@dataclass(frozen=True)
class UpdatePremiseRequest:
    tenant_id: UUID
    premise_id: UUID
    name: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class UpdatePremiseUseCase:

    def __init__(self, premise_repo: PremiseRepositoryPort) -> None:
        self._repo = premise_repo

    async def execute(self, request: UpdatePremiseRequest):
        premise = await self._repo.get_by_id(request.tenant_id, request.premise_id)
        if not premise:
            raise ValueError("Premise not found")

        if request.name is not None:
            premise.name = request.name
        if request.type is not None:
            premise.type = PremiseType(request.type)
        if request.value is not None:
            premise.value = request.value
        if request.description is not None:
            premise.description = request.description
        if request.is_active is not None:
            premise.is_active = request.is_active

        premise.updated_at = datetime.utcnow()
        await self._repo.update(premise)
        return premise
