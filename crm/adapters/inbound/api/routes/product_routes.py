from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.dependencies import (
    get_add_stock_movement_uc,
    get_create_product_uc,
    get_generate_stock_report_uc,
    get_list_products_uc,
    get_list_stock_movements_uc,
    get_update_product_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.persistence.database import get_session
from core.domain.product import MovementType, Product, StockMovement
from core.use_cases.inventory.add_stock_movement import AddStockMovementRequest, AddStockMovementUseCase
from core.use_cases.inventory.create_product import CreateProductRequest, CreateProductUseCase
from core.use_cases.inventory.generate_stock_report import GenerateStockReportUseCase
from core.use_cases.inventory.list_products import ListProductsUseCase
from core.use_cases.inventory.list_stock_movements import ListStockMovementsUseCase
from core.use_cases.inventory.update_product import UpdateProductRequest, UpdateProductUseCase

router = APIRouter(prefix="/api/v1/products", tags=["products"])


# --- Schemas ---

class ProductCreateBody(BaseModel):
    name: str
    sku: str
    unit: str = "un"
    price: Optional[float] = None
    cost: Optional[float] = None
    stock_quantity: float = 0.0
    min_stock_alert: float = 0.0
    description: str = ""


class ProductUpdateBody(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    min_stock_alert: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StockMovementBody(BaseModel):
    type: str   # "in", "out", "adjustment"
    quantity: float
    reason: str = ""
    reference_id: Optional[str] = None


class ProductOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    sku: str
    unit: str
    price: Optional[float] = None
    cost: Optional[float] = None
    stock_quantity: float
    min_stock_alert: float
    is_low_stock: bool
    description: str
    is_active: bool
    created_at: str
    updated_at: str


class StockMovementOut(BaseModel):
    id: str
    product_id: str
    type: str
    quantity: float
    reason: str
    reference_id: Optional[str] = None
    created_at: str


class StockMovementResultOut(BaseModel):
    movement: StockMovementOut
    new_stock_quantity: float
    is_low_stock: bool


class PaginatedProducts(BaseModel):
    items: list[ProductOut]
    total: int
    offset: int
    limit: int


class PaginatedMovements(BaseModel):
    items: list[StockMovementOut]
    total: int
    offset: int
    limit: int


def _product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=str(p.id),
        tenant_id=str(p.tenant_id),
        name=p.name,
        sku=p.sku,
        unit=p.unit,
        price=p.price,
        cost=p.cost,
        stock_quantity=p.stock_quantity,
        min_stock_alert=p.min_stock_alert,
        is_low_stock=p.is_low_stock,
        description=p.description,
        is_active=p.is_active,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


def _movement_out(m: StockMovement) -> StockMovementOut:
    return StockMovementOut(
        id=str(m.id),
        product_id=str(m.product_id),
        type=m.type.value if isinstance(m.type, MovementType) else m.type,
        quantity=m.quantity,
        reason=m.reason,
        reference_id=str(m.reference_id) if m.reference_id else None,
        created_at=m.created_at.isoformat(),
    )


# --- Routes ---

@router.get("", response_model=PaginatedProducts)
async def list_products(
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    low_stock_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListProductsUseCase = Depends(get_list_products_uc),
):
    result = await uc.execute(
        current_user.tenant_id,
        search=search,
        active_only=active_only,
        low_stock_only=low_stock_only,
        offset=offset,
        limit=limit,
    )
    return PaginatedProducts(
        items=[_product_out(p) for p in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreateProductUseCase = Depends(get_create_product_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        product = await uc.execute(CreateProductRequest(
            tenant_id=current_user.tenant_id,
            name=body.name,
            sku=body.sku,
            unit=body.unit,
            price=body.price,
            cost=body.cost,
            stock_quantity=body.stock_quantity,
            min_stock_alert=body.min_stock_alert,
            description=body.description,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    return _product_out(product)


@router.get("/report/pdf")
async def generate_stock_report(
    current_user: CurrentUser = Depends(get_current_user),
    uc: GenerateStockReportUseCase = Depends(get_generate_stock_report_uc),
):
    try:
        pdf_bytes = await uc.execute(current_user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio-estoque.pdf"},
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateProductUseCase = Depends(get_update_product_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        await uc.execute(UpdateProductRequest(
            tenant_id=current_user.tenant_id,
            product_id=product_id,
            is_active=False,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await session.commit()
    return Response(status_code=204)


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: UUID,
    body: ProductUpdateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateProductUseCase = Depends(get_update_product_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        product = await uc.execute(UpdateProductRequest(
            tenant_id=current_user.tenant_id,
            product_id=product_id,
            name=body.name,
            unit=body.unit,
            price=body.price,
            cost=body.cost,
            min_stock_alert=body.min_stock_alert,
            description=body.description,
            is_active=body.is_active,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await session.commit()
    return _product_out(product)


@router.post("/{product_id}/stock-movements", response_model=StockMovementResultOut, status_code=201)
async def add_stock_movement(
    product_id: UUID,
    body: StockMovementBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: AddStockMovementUseCase = Depends(get_add_stock_movement_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await uc.execute(AddStockMovementRequest(
            tenant_id=current_user.tenant_id,
            product_id=product_id,
            type=body.type,
            quantity=body.quantity,
            reason=body.reason,
            reference_id=UUID(body.reference_id) if body.reference_id else None,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    return StockMovementResultOut(
        movement=_movement_out(result.movement),
        new_stock_quantity=result.new_stock_quantity,
        is_low_stock=result.is_low_stock,
    )


@router.get("/{product_id}/stock-movements", response_model=PaginatedMovements)
async def list_stock_movements(
    product_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListStockMovementsUseCase = Depends(get_list_stock_movements_uc),
):
    try:
        result = await uc.execute(
            current_user.tenant_id, product_id, offset=offset, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PaginatedMovements(
        items=[_movement_out(m) for m in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )
