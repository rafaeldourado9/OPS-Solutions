from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from core.domain.premise import Premise


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class QuoteItem:
    id: UUID
    quote_id: UUID
    description: str
    quantity: float
    unit_price: float
    discount: float = 0.0  # percentage 0-100
    notes: str = ""

    @property
    def subtotal(self) -> float:
        gross = self.quantity * self.unit_price
        return gross * (1 - self.discount / 100)

    @staticmethod
    def create(
        quote_id: UUID,
        description: str,
        quantity: float,
        unit_price: float,
        discount: float = 0.0,
        notes: str = "",
    ) -> QuoteItem:
        return QuoteItem(
            id=uuid4(),
            quote_id=quote_id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            discount=discount,
            notes=notes,
        )


@dataclass
class AppliedPremise:
    premise_id: UUID
    name: str
    type: str
    value: float
    amount: float  # computed amount applied to the quote


@dataclass
class Quote:
    id: UUID
    tenant_id: UUID
    customer_id: Optional[UUID]
    lead_id: Optional[UUID]
    title: str
    status: QuoteStatus
    items: list[QuoteItem] = field(default_factory=list)
    applied_premises: list[AppliedPremise] = field(default_factory=list)
    notes: str = ""
    valid_until: Optional[datetime] = None
    currency: str = "BRL"
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @property
    def items_total(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def premises_total(self) -> float:
        return sum(ap.amount for ap in self.applied_premises)

    @property
    def total(self) -> float:
        return self.items_total + self.premises_total

    @staticmethod
    def create(
        tenant_id: UUID,
        title: str,
        customer_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        notes: str = "",
        valid_until: Optional[datetime] = None,
        currency: str = "BRL",
    ) -> Quote:
        now = datetime.utcnow()
        return Quote(
            id=uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            lead_id=lead_id,
            title=title,
            status=QuoteStatus.DRAFT,
            notes=notes,
            valid_until=valid_until,
            currency=currency,
            created_at=now,
            updated_at=now,
        )

    def apply_premises(self, premises: list[Premise]) -> None:
        """Recalculates applied_premises based on current items_total."""
        base = self.items_total
        self.applied_premises = [
            AppliedPremise(
                premise_id=p.id,
                name=p.name,
                type=p.type.value,
                value=p.value,
                amount=p.apply_to(base),
            )
            for p in premises
        ]
        self.updated_at = datetime.utcnow()

    def can_transition_to(self, target: QuoteStatus) -> bool:
        allowed: dict[QuoteStatus, list[QuoteStatus]] = {
            QuoteStatus.DRAFT: [QuoteStatus.SENT, QuoteStatus.EXPIRED],
            QuoteStatus.SENT: [QuoteStatus.APPROVED, QuoteStatus.REJECTED, QuoteStatus.EXPIRED],
            QuoteStatus.APPROVED: [],
            QuoteStatus.REJECTED: [QuoteStatus.DRAFT],
            QuoteStatus.EXPIRED: [QuoteStatus.DRAFT],
        }
        return target in allowed.get(self.status, [])
