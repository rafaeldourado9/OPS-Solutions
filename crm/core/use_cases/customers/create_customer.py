from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import structlog

from core.domain.customer import Customer
from core.ports.outbound.customer_repository import CustomerRepositoryPort

logger = structlog.get_logger()


@dataclass(frozen=True)
class CreateCustomerRequest:
    tenant_id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    company_name: Optional[str] = None
    source: str = "manual"
    chat_id: Optional[str] = None
    tags: list[str] | None = None
    notes: str = ""


class CreateCustomerUseCase:

    def __init__(self, customer_repo: CustomerRepositoryPort) -> None:
        self._repo = customer_repo

    async def execute(self, request: CreateCustomerRequest) -> Customer:
        existing = await self._repo.get_by_phone(request.tenant_id, request.phone)
        if existing:
            raise ValueError(f"Customer with phone '{request.phone}' already exists")

        customer = Customer.create(
            tenant_id=request.tenant_id,
            name=request.name,
            phone=request.phone,
            source=request.source,
            chat_id=request.chat_id,
            email=request.email,
        )
        customer.cpf_cnpj = request.cpf_cnpj
        customer.company_name = request.company_name
        customer.notes = request.notes
        if request.tags:
            customer.tags = request.tags

        await self._repo.save(customer)

        logger.info("customer_created", customer_id=str(customer.id), phone=customer.phone)
        return customer
