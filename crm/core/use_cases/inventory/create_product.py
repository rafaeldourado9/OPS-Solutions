from dataclasses import dataclass
from uuid import UUID

from core.domain.product import Product
from core.ports.outbound.product_repository import ProductRepositoryPort


@dataclass(frozen=True)
class CreateProductRequest:
    tenant_id: UUID
    name: str
    sku: str
    unit: str = "un"
    price: float = 0.0
    cost: float = 0.0
    stock_quantity: float = 0.0
    min_stock_alert: float = 0.0
    description: str = ""


class CreateProductUseCase:

    def __init__(self, product_repo: ProductRepositoryPort) -> None:
        self._repo = product_repo

    async def execute(self, request: CreateProductRequest) -> Product:
        existing = await self._repo.get_by_sku(request.tenant_id, request.sku)
        if existing:
            raise ValueError(f"Product with SKU '{request.sku}' already exists")

        product = Product.create(
            tenant_id=request.tenant_id,
            name=request.name,
            sku=request.sku,
            unit=request.unit,
            price=request.price,
            cost=request.cost,
            stock_quantity=request.stock_quantity,
            min_stock_alert=request.min_stock_alert,
            description=request.description,
        )
        await self._repo.save(product)
        return product
