from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.product import Product
from core.ports.outbound.product_repository import ProductRepositoryPort


@dataclass
class ListProductsResult:
    items: list[Product]
    total: int
    offset: int
    limit: int


class ListProductsUseCase:

    def __init__(self, product_repo: ProductRepositoryPort) -> None:
        self._repo = product_repo

    async def execute(
        self,
        tenant_id: UUID,
        search: Optional[str] = None,
        active_only: bool = True,
        low_stock_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> ListProductsResult:
        items, total = await self._repo.list_by_tenant(
            tenant_id,
            search=search,
            active_only=active_only,
            low_stock_only=low_stock_only,
            offset=offset,
            limit=limit,
        )
        return ListProductsResult(items=items, total=total, offset=offset, limit=limit)
