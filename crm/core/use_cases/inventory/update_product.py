from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.product import Product
from core.ports.outbound.product_repository import ProductRepositoryPort


@dataclass(frozen=True)
class UpdateProductRequest:
    tenant_id: UUID
    product_id: UUID
    name: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    min_stock_alert: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class UpdateProductUseCase:

    def __init__(self, product_repo: ProductRepositoryPort) -> None:
        self._repo = product_repo

    async def execute(self, request: UpdateProductRequest) -> Product:
        product = await self._repo.get_by_id(request.tenant_id, request.product_id)
        if not product:
            raise ValueError("Product not found")

        if request.name is not None:
            product.name = request.name
        if request.unit is not None:
            product.unit = request.unit
        if request.price is not None:
            product.price = request.price
        if request.cost is not None:
            product.cost = request.cost
        if request.min_stock_alert is not None:
            product.min_stock_alert = request.min_stock_alert
        if request.description is not None:
            product.description = request.description
        if request.is_active is not None:
            product.is_active = request.is_active

        product.updated_at = datetime.utcnow()
        await self._repo.update(product)
        return product
