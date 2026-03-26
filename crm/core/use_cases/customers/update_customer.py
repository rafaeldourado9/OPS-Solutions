from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.customer import Address, Customer
from core.ports.outbound.customer_repository import CustomerRepositoryPort


@dataclass
class UpdateCustomerRequest:
    tenant_id: UUID
    customer_id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    company_name: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    address: Optional[dict] = None


class UpdateCustomerUseCase:

    def __init__(self, customer_repo: CustomerRepositoryPort) -> None:
        self._repo = customer_repo

    async def execute(self, request: UpdateCustomerRequest) -> Customer:
        customer = await self._repo.get_by_id(request.tenant_id, request.customer_id)
        if not customer:
            raise ValueError("Customer not found")

        if request.name is not None:
            customer.name = request.name
        if request.email is not None:
            customer.email = request.email
        if request.cpf_cnpj is not None:
            customer.cpf_cnpj = request.cpf_cnpj
        if request.company_name is not None:
            customer.company_name = request.company_name
        if request.tags is not None:
            customer.tags = request.tags
        if request.notes is not None:
            customer.notes = request.notes
        if request.address is not None:
            customer.address = Address(**request.address)

        customer.updated_at = datetime.utcnow()
        await self._repo.update(customer)
        return customer
