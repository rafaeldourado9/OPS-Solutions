from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from adapters.outbound.persistence.models.product_model import ProductModel, StockMovementModel
from core.domain.product import MovementType, Product, StockMovement
from core.ports.outbound.product_repository import ProductRepositoryPort
from core.ports.outbound.stock_movement_repository import StockMovementRepositoryPort


class PgProductRepository(ProductRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, product: Product) -> None:
        self._session.add(self._to_model(product))
        await self._session.flush()

    async def update(self, product: Product) -> None:
        stmt = (
            update(ProductModel)
            .where(ProductModel.id == product.id, ProductModel.tenant_id == product.tenant_id)
            .values(
                name=product.name,
                unit=product.unit,
                price=product.price,
                cost=product.cost,
                stock_quantity=product.stock_quantity,
                min_stock_alert=product.min_stock_alert,
                description=product.description,
                is_active=product.is_active,
                updated_at=product.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, product_id: UUID) -> Optional[Product]:
        stmt = select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_sku(self, tenant_id: UUID, sku: str) -> Optional[Product]:
        stmt = select(ProductModel).where(
            ProductModel.sku == sku,
            ProductModel.tenant_id == tenant_id,
            ProductModel.is_active == True,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        search: Optional[str] = None,
        active_only: bool = True,
        low_stock_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Product], int]:
        base = select(ProductModel).where(ProductModel.tenant_id == tenant_id)
        if active_only:
            base = base.where(ProductModel.is_active == True)  # noqa: E712
        if search:
            base = base.where(
                ProductModel.name.ilike(f"%{search}%") | ProductModel.sku.ilike(f"%{search}%")
            )
        if low_stock_only:
            base = base.where(ProductModel.stock_quantity <= ProductModel.min_stock_alert)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        query = base.order_by(ProductModel.name).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()], total

    @staticmethod
    def _to_model(p: Product) -> ProductModel:
        return ProductModel(
            id=p.id,
            tenant_id=p.tenant_id,
            name=p.name,
            sku=p.sku,
            unit=p.unit,
            price=p.price,
            cost=p.cost,
            stock_quantity=p.stock_quantity,
            min_stock_alert=p.min_stock_alert,
            description=p.description,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @staticmethod
    def _to_domain(m: ProductModel) -> Product:
        return Product(
            id=m.id,
            tenant_id=m.tenant_id,
            name=m.name,
            sku=m.sku,
            unit=m.unit,
            price=m.price,
            cost=m.cost,
            stock_quantity=m.stock_quantity,
            min_stock_alert=m.min_stock_alert,
            description=m.description,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class PgStockMovementRepository(StockMovementRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, movement: StockMovement) -> None:
        model = StockMovementModel(
            id=movement.id,
            tenant_id=movement.tenant_id,
            product_id=movement.product_id,
            type=movement.type.value if isinstance(movement.type, MovementType) else movement.type,
            quantity=movement.quantity,
            reason=movement.reason,
            reference_id=movement.reference_id,
            created_at=movement.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_by_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockMovement], int]:
        base = select(StockMovementModel).where(
            StockMovementModel.tenant_id == tenant_id,
            StockMovementModel.product_id == product_id,
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        query = base.order_by(StockMovementModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        movements = [
            StockMovement(
                id=m.id,
                tenant_id=m.tenant_id,
                product_id=m.product_id,
                type=MovementType(m.type),
                quantity=m.quantity,
                reason=m.reason,
                reference_id=m.reference_id,
                created_at=m.created_at,
            )
            for m in result.scalars().all()
        ]
        return movements, total

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        product_ids: Optional[list[UUID]] = None,
        offset: int = 0,
        limit: int = 500,
    ) -> tuple[list[StockMovement], int]:
        base = select(StockMovementModel).where(StockMovementModel.tenant_id == tenant_id)
        if product_ids:
            base = base.where(StockMovementModel.product_id.in_(product_ids))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        query = base.order_by(StockMovementModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        movements = [
            StockMovement(
                id=m.id,
                tenant_id=m.tenant_id,
                product_id=m.product_id,
                type=MovementType(m.type),
                quantity=m.quantity,
                reason=m.reason,
                reference_id=m.reference_id,
                created_at=m.created_at,
            )
            for m in result.scalars().all()
        ]
        return movements, total
