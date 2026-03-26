from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class LeadStage(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


# Valid stage transitions (Kanban flow)
STAGE_TRANSITIONS: dict[LeadStage, list[LeadStage]] = {
    LeadStage.NEW: [LeadStage.CONTACTED, LeadStage.LOST],
    LeadStage.CONTACTED: [LeadStage.QUALIFIED, LeadStage.LOST],
    LeadStage.QUALIFIED: [LeadStage.PROPOSAL, LeadStage.LOST],
    LeadStage.PROPOSAL: [LeadStage.NEGOTIATION, LeadStage.LOST],
    LeadStage.NEGOTIATION: [LeadStage.WON, LeadStage.LOST],
    LeadStage.WON: [],
    LeadStage.LOST: [LeadStage.NEW],  # Allow reopening
}


@dataclass
class Lead:
    id: UUID
    tenant_id: UUID
    customer_id: Optional[UUID]
    title: str
    stage: LeadStage
    value: float = 0.0
    currency: str = "BRL"
    source: str = ""  # whatsapp, website, referral, manual, etc.
    assigned_to: Optional[UUID] = None  # user_id of the salesperson
    notes: str = ""
    expected_close_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    lost_reason: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        title: str,
        customer_id: Optional[UUID] = None,
        value: float = 0.0,
        source: str = "manual",
        assigned_to: Optional[UUID] = None,
        notes: str = "",
        expected_close_date: Optional[datetime] = None,
        tags: list[str] | None = None,
    ) -> Lead:
        now = datetime.utcnow()
        return Lead(
            id=uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            title=title,
            stage=LeadStage.NEW,
            value=value,
            source=source,
            assigned_to=assigned_to,
            notes=notes,
            expected_close_date=expected_close_date,
            tags=tags or [],
            created_at=now,
            updated_at=now,
        )

    def can_move_to(self, target: LeadStage) -> bool:
        return target in STAGE_TRANSITIONS.get(self.stage, [])

    def move_to(self, target: LeadStage, lost_reason: str = "") -> None:
        if not self.can_move_to(target):
            raise ValueError(
                f"Cannot move from '{self.stage.value}' to '{target.value}'"
            )
        self.stage = target
        self.updated_at = datetime.utcnow()

        if target == LeadStage.WON:
            self.closed_at = self.updated_at
        elif target == LeadStage.LOST:
            self.closed_at = self.updated_at
            self.lost_reason = lost_reason
        elif target == LeadStage.NEW:
            # Reopening
            self.closed_at = None
            self.lost_reason = ""
