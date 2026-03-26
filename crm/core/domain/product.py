from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class MovementType(str, Enum):
    IN = "in"           # entrada
    OUT = "out"         # saida
    ADJUSTMENT = "adjustment"  # ajuste manual


@dataclass
class StockMovement:
    id: UUID
    tenant_id: UUID
    product_id: UUID
    type: MovementType
    quantity: float     # always positive; direction determined by type
    reason: str = ""
    reference_id: Optional[UUID] = None  # e.g. quote_id that consumed stock
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        product_id: UUID,
        type: MovementType,
        quantity: float,
        reason: str = "",
        reference_id: Optional[UUID] = None,
    ) -> StockMovement:
        if quantity <= 0:
            raise ValueError("Stock movement quantity must be positive")
        return StockMovement(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product_id,
            type=type,
            quantity=quantity,
            reason=reason,
            reference_id=reference_id,
            created_at=datetime.utcnow(),
        )


@dataclass
class Product:
    id: UUID
    tenant_id: UUID
    name: str
    sku: str
    unit: str           # un, m, kg, L, etc.
    price: float        # sale price
    cost: float         # purchase cost
    stock_quantity: float
    min_stock_alert: float  # alert threshold
    description: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        sku: str,
        unit: str = "un",
        price: float = 0.0,
        cost: float = 0.0,
        stock_quantity: float = 0.0,
        min_stock_alert: float = 0.0,
        description: str = "",
    ) -> Product:
        now = datetime.utcnow()
        return Product(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            sku=sku,
            unit=unit,
            price=price,
            cost=cost,
            stock_quantity=stock_quantity,
            min_stock_alert=min_stock_alert,
            description=description,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.min_stock_alert

    def apply_movement(self, movement: StockMovement) -> None:
        if movement.type == MovementType.IN:
            self.stock_quantity += movement.quantity
        elif movement.type == MovementType.OUT:
            if movement.quantity > self.stock_quantity:
                raise ValueError(
                    f"Insufficient stock: have {self.stock_quantity}, need {movement.quantity}"
                )
            self.stock_quantity -= movement.quantity
        elif movement.type == MovementType.ADJUSTMENT:
            self.stock_quantity = movement.quantity  # absolute value for adjustment
        self.updated_at = datetime.utcnow()
