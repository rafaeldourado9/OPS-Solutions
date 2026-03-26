from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.product import Product


class ProductRepositoryPort(ABC):

    @abstractmethod
    async def save(self, product: Product) -> None: ...

    @abstractmethod
    async def update(self, product: Product) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, product_id: UUID) -> Optional[Product]: ...

    @abstractmethod
    async def get_by_sku(self, tenant_id: UUID, sku: str) -> Optional[Product]: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        search: Optional[str] = None,
        active_only: bool = True,
        low_stock_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Product], int]: ...
