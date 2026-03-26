from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class PremiseType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


@dataclass
class Premise:
    id: UUID
    tenant_id: UUID
    name: str
    type: PremiseType
    value: float  # percentage (0-100) or fixed monetary amount
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
        description: str = "",
    ) -> Premise:
        now = datetime.utcnow()
        return Premise(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            type=type,
            value=value,
            description=description,
            created_at=now,
            updated_at=now,
        )

    def apply_to(self, base_value: float) -> float:
        """Returns the amount to add on top of base_value."""
        if self.type == PremiseType.PERCENTAGE:
            return base_value * (self.value / 100)
        return self.value
