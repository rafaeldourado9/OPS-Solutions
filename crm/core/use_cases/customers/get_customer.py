from uuid import UUID

from core.domain.customer import Customer
from core.ports.outbound.customer_repository import CustomerRepositoryPort


class GetCustomerUseCase:

    def __init__(self, customer_repo: CustomerRepositoryPort) -> None:
        self._repo = customer_repo

    async def execute(self, tenant_id: UUID, customer_id: UUID) -> Customer:
        customer = await self._repo.get_by_id(tenant_id, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        return customer
