from dataclasses import dataclass
from uuid import UUID

from core.domain.product import StockMovement
from core.ports.outbound.product_repository import ProductRepositoryPort
from core.ports.outbound.stock_movement_repository import StockMovementRepositoryPort


@dataclass
class ListStockMovementsResult:
    items: list[StockMovement]
    total: int
    offset: int
    limit: int


class ListStockMovementsUseCase:

    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        movement_repo: StockMovementRepositoryPort,
    ) -> None:
        self._product_repo = product_repo
        self._movement_repo = movement_repo

    async def execute(
        self,
        tenant_id: UUID,
        product_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> ListStockMovementsResult:
        product = await self._product_repo.get_by_id(tenant_id, product_id)
        if not product:
            raise ValueError("Product not found")

        items, total = await self._movement_repo.list_by_product(
            tenant_id, product_id, offset=offset, limit=limit
        )
        return ListStockMovementsResult(items=items, total=total, offset=offset, limit=limit)
