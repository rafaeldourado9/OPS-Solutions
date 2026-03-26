import pytest

from core.domain.product import MovementType
from core.use_cases.inventory.add_stock_movement import AddStockMovementRequest, AddStockMovementUseCase
from core.use_cases.inventory.create_product import CreateProductRequest, CreateProductUseCase
from core.use_cases.inventory.list_products import ListProductsUseCase
from core.use_cases.inventory.list_stock_movements import ListStockMovementsUseCase
from core.use_cases.inventory.update_product import UpdateProductRequest, UpdateProductUseCase


@pytest.fixture
def create_uc(product_repo):
    return CreateProductUseCase(product_repo)


@pytest.fixture
def movement_uc(product_repo, stock_movement_repo):
    return AddStockMovementUseCase(product_repo, stock_movement_repo)


async def test_create_product(create_uc, sample_tenant):
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id,
        name="Cabo 10mm",
        sku="CAB-10",
        unit="m",
        price=8.50,
        cost=5.0,
        stock_quantity=100.0,
        min_stock_alert=20.0,
    ))

    assert product.name == "Cabo 10mm"
    assert product.sku == "CAB-10"
    assert product.stock_quantity == 100.0
    assert product.is_low_stock is False


async def test_create_product_duplicate_sku_raises(create_uc, sample_tenant):
    await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P1", sku="SKU-001"
    ))
    with pytest.raises(ValueError, match="already exists"):
        await create_uc.execute(CreateProductRequest(
            tenant_id=sample_tenant.id, name="P2", sku="SKU-001"
        ))


async def test_stock_in(create_uc, movement_uc, sample_tenant):
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P", sku="S1", stock_quantity=10.0
    ))

    result = await movement_uc.execute(AddStockMovementRequest(
        tenant_id=sample_tenant.id,
        product_id=product.id,
        type="in",
        quantity=50.0,
        reason="Compra fornecedor",
    ))

    assert result.new_stock_quantity == 60.0
    assert result.movement.type == MovementType.IN


async def test_stock_out(create_uc, movement_uc, sample_tenant):
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P", sku="S2", stock_quantity=100.0
    ))

    result = await movement_uc.execute(AddStockMovementRequest(
        tenant_id=sample_tenant.id,
        product_id=product.id,
        type="out",
        quantity=30.0,
        reason="Venda",
    ))

    assert result.new_stock_quantity == 70.0


async def test_stock_out_insufficient_raises(create_uc, movement_uc, sample_tenant):
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P", sku="S3", stock_quantity=5.0
    ))

    with pytest.raises(ValueError, match="Insufficient stock"):
        await movement_uc.execute(AddStockMovementRequest(
            tenant_id=sample_tenant.id,
            product_id=product.id,
            type="out",
            quantity=10.0,
        ))


async def test_stock_adjustment(create_uc, movement_uc, sample_tenant):
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P", sku="S4", stock_quantity=100.0
    ))

    result = await movement_uc.execute(AddStockMovementRequest(
        tenant_id=sample_tenant.id,
        product_id=product.id,
        type="adjustment",
        quantity=42.0,
        reason="Inventário físico",
    ))

    assert result.new_stock_quantity == 42.0


async def test_low_stock_alert(create_uc, movement_uc, sample_tenant):
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P", sku="S5",
        stock_quantity=25.0, min_stock_alert=20.0,
    ))

    result = await movement_uc.execute(AddStockMovementRequest(
        tenant_id=sample_tenant.id,
        product_id=product.id,
        type="out",
        quantity=10.0,
    ))

    assert result.new_stock_quantity == 15.0
    assert result.is_low_stock is True


async def test_list_products_with_low_stock_filter(
    product_repo, stock_movement_repo, sample_tenant
):
    create_uc = CreateProductUseCase(product_repo)
    movement_uc = AddStockMovementUseCase(product_repo, stock_movement_repo)

    p1 = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="Normal", sku="N1",
        stock_quantity=100.0, min_stock_alert=10.0,
    ))
    p2 = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="Baixo", sku="N2",
        stock_quantity=5.0, min_stock_alert=10.0,
    ))

    list_uc = ListProductsUseCase(product_repo)
    result = await list_uc.execute(sample_tenant.id, low_stock_only=True)

    assert result.total == 1
    assert result.items[0].id == p2.id


async def test_list_stock_movements(
    product_repo, stock_movement_repo, sample_tenant
):
    create_uc = CreateProductUseCase(product_repo)
    movement_uc = AddStockMovementUseCase(product_repo, stock_movement_repo)

    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="P", sku="M1", stock_quantity=100.0
    ))
    await movement_uc.execute(AddStockMovementRequest(
        tenant_id=sample_tenant.id, product_id=product.id, type="out", quantity=10.0
    ))
    await movement_uc.execute(AddStockMovementRequest(
        tenant_id=sample_tenant.id, product_id=product.id, type="in", quantity=50.0
    ))

    list_uc = ListStockMovementsUseCase(product_repo, stock_movement_repo)
    result = await list_uc.execute(sample_tenant.id, product.id)

    assert result.total == 2


async def test_update_product(product_repo, sample_tenant):
    create_uc = CreateProductUseCase(product_repo)
    product = await create_uc.execute(CreateProductRequest(
        tenant_id=sample_tenant.id, name="Old Name", sku="U1", price=10.0
    ))

    update_uc = UpdateProductUseCase(product_repo)
    updated = await update_uc.execute(UpdateProductRequest(
        tenant_id=sample_tenant.id,
        product_id=product.id,
        name="New Name",
        price=15.0,
    ))

    assert updated.name == "New Name"
    assert updated.price == 15.0
    assert updated.sku == "U1"  # unchanged
