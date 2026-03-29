from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class PremiseType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    MULTIPLIER = "multiplier"  # cost × factor → selling price contribution


@dataclass
class Premise:
    id: UUID
    tenant_id: UUID
    name: str
    type: PremiseType
    value: float  # percentage (0-100) | fixed amount | multiplier factor (e.g. 2.5)
    cost: float = 0.0  # base cost for MULTIPLIER type (e.g. R$ 1.000,00)
    description: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        type: PremiseType,
        value: float,
        cost: float = 0.0,
        description: str = "",
    ) -> Premise:
        now = datetime.utcnow()
        return Premise(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            type=type,
            value=value,
            cost=cost,
            description=description,
            created_at=now,
            updated_at=now,
        )

    def apply_to(self, base_value: float) -> float:
        """Returns the amount to add on top of base_value.

        - PERCENTAGE : base_value × (value / 100)
        - FIXED      : value  (independent of base)
        - MULTIPLIER : cost × value  (cost × factor, independent of base)
                       e.g. cost=1000, factor=2.5 → adds R$ 2.500 to the quote
        """
        if self.type == PremiseType.PERCENTAGE:
            return base_value * (self.value / 100)
        if self.type == PremiseType.MULTIPLIER:
            return self.cost * self.value
        return self.value  # FIXED
