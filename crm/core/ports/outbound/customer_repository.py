from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.customer import Customer


class CustomerRepositoryPort(ABC):

    @abstractmethod
    async def save(self, customer: Customer) -> None: ...

    @abstractmethod
    async def update(self, customer: Customer) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, customer_id: UUID) -> Optional[Customer]: ...

    @abstractmethod
    async def get_by_phone(self, tenant_id: UUID, phone: str) -> Optional[Customer]: ...

    @abstractmethod
    async def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[Customer]: ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> tuple[list[Customer], int]: ...

    @abstractmethod
    async def delete(self, tenant_id: UUID, customer_id: UUID) -> bool: ...
