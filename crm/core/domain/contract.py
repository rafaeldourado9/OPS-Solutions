from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Contract:
    id: UUID
    tenant_id: UUID
    quote_id: UUID
    customer_id: Optional[UUID]
    title: str
    status: ContractStatus
    content: str = ""       # free-text contract body
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create_from_quote(
        tenant_id: UUID,
        quote_id: UUID,
        title: str,
        customer_id: Optional[UUID] = None,
        content: str = "",
        expires_at: Optional[datetime] = None,
    ) -> Contract:
        now = datetime.utcnow()
        return Contract(
            id=uuid4(),
            tenant_id=tenant_id,
            quote_id=quote_id,
            customer_id=customer_id,
            title=title,
            status=ContractStatus.DRAFT,
            content=content,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )

    def can_transition_to(self, target: ContractStatus) -> bool:
        allowed: dict[ContractStatus, list[ContractStatus]] = {
            ContractStatus.DRAFT: [ContractStatus.ACTIVE, ContractStatus.CANCELLED],
            ContractStatus.ACTIVE: [ContractStatus.COMPLETED, ContractStatus.CANCELLED],
            ContractStatus.COMPLETED: [],
            ContractStatus.CANCELLED: [ContractStatus.DRAFT],
        }
        return target in allowed.get(self.status, [])
