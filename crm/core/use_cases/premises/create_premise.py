from dataclasses import dataclass
from uuid import UUID

from core.domain.premise import Premise, PremiseType
from core.ports.outbound.premise_repository import PremiseRepositoryPort


@dataclass(frozen=True)
class CreatePremiseRequest:
    tenant_id: UUID
    name: str
    type: str  # "percentage" | "fixed" | "multiplier"
    value: float
    cost: float = 0.0
    description: str = ""


class CreatePremiseUseCase:

    def __init__(self, premise_repo: PremiseRepositoryPort) -> None:
        self._repo = premise_repo

    async def execute(self, request: CreatePremiseRequest) -> Premise:
        premise = Premise.create(
            tenant_id=request.tenant_id,
            name=request.name,
            type=PremiseType(request.type),
            value=request.value,
            cost=request.cost,
            description=request.description,
        )
        await self._repo.save(premise)
        return premise
