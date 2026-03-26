from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.quote import Quote, QuoteItem


class QuoteRepositoryPort(ABC):

    @abstractmethod
    async def save(self, quote: Quote) -> None: ...

    @abstractmethod
    async def update(self, quote: Quote) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, quote_id: UUID) -> Optional[Quote]: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Quote], int]: ...

    @abstractmethod
    async def delete(self, tenant_id: UUID, quote_id: UUID) -> bool: ...
