from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.domain.contract import Contract, ContractStatus
from core.ports.outbound.contract_repository import ContractRepositoryPort


@dataclass(frozen=True)
class UpdateContractStatusRequest:
    tenant_id: UUID
    contract_id: UUID
    status: str


class UpdateContractStatusUseCase:

    def __init__(self, contract_repo: ContractRepositoryPort) -> None:
        self._repo = contract_repo

    async def execute(self, request: UpdateContractStatusRequest) -> Contract:
        contract = await self._repo.get_by_id(request.tenant_id, request.contract_id)
        if not contract:
            raise ValueError("Contract not found")

        target = ContractStatus(request.status)
        if not contract.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from '{contract.status.value}' to '{target.value}'"
            )

        contract.status = target
        now = datetime.utcnow()
        contract.updated_at = now

        if target == ContractStatus.ACTIVE:
            contract.signed_at = now

        await self._repo.update(contract)
        return contract
