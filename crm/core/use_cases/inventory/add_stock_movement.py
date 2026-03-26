from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.product import MovementType, StockMovement
from core.ports.outbound.product_repository import ProductRepositoryPort
from core.ports.outbound.stock_movement_repository import StockMovementRepositoryPort


@dataclass(frozen=True)
class AddStockMovementRequest:
    tenant_id: UUID
    product_id: UUID
    type: str   # "in", "out", "adjustment"
    quantity: float
    reason: str = ""
    reference_id: Optional[UUID] = None


@dataclass
class StockMovementResult:
    movement: StockMovement
    new_stock_quantity: float
    is_low_stock: bool


class AddStockMovementUseCase:

    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        movement_repo: StockMovementRepositoryPort,
    ) -> None:
        self._product_repo = product_repo
        self._movement_repo = movement_repo

    async def execute(self, request: AddStockMovementRequest) -> StockMovementResult:
        product = await self._product_repo.get_by_id(request.tenant_id, request.product_id)
        if not product:
            raise ValueError("Product not found")

        movement = StockMovement.create(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            type=MovementType(request.type),
            quantity=request.quantity,
            reason=request.reason,
            reference_id=request.reference_id,
        )

        product.apply_movement(movement)
        await self._product_repo.update(product)
        await self._movement_repo.save(movement)

        return StockMovementResult(
            movement=movement,
            new_stock_quantity=product.stock_quantity,
            is_low_stock=product.is_low_stock,
        )
