from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.product import StockMovement


class StockMovementRepositoryPort(ABC):

    @abstractmethod
    async def save(self, movement: StockMovement) -> None: ...

    @abstractmethod
    async def list_by_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockMovement], int]: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        product_ids: Optional[list[UUID]] = None,
        offset: int = 0,
        limit: int = 500,
    ) -> tuple[list[StockMovement], int]: ...
