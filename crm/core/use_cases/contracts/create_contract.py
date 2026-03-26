from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.contract import Contract
from core.domain.quote import QuoteStatus
from core.ports.outbound.contract_repository import ContractRepositoryPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort


@dataclass(frozen=True)
class CreateContractRequest:
    tenant_id: UUID
    quote_id: UUID
    title: str
    content: str = ""
    expires_at: Optional[datetime] = None


class CreateContractUseCase:

    def __init__(
        self,
        contract_repo: ContractRepositoryPort,
        quote_repo: QuoteRepositoryPort,
    ) -> None:
        self._contract_repo = contract_repo
        self._quote_repo = quote_repo

    async def execute(self, request: CreateContractRequest) -> Contract:
        quote = await self._quote_repo.get_by_id(request.tenant_id, request.quote_id)
        if not quote:
            raise ValueError("Quote not found")
        if quote.status != QuoteStatus.APPROVED:
            raise ValueError("Contract can only be created from an approved quote")

        existing = await self._contract_repo.get_by_quote_id(request.tenant_id, request.quote_id)
        if existing:
            raise ValueError("A contract already exists for this quote")

        contract = Contract.create_from_quote(
            tenant_id=request.tenant_id,
            quote_id=request.quote_id,
            title=request.title,
            customer_id=quote.customer_id,
            content=request.content,
            expires_at=request.expires_at,
        )
        await self._contract_repo.save(contract)
        return contract
