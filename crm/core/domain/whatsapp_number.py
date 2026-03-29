from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class WhatsAppNumber:
    id: UUID
    tenant_id: UUID
    session_name: str
    phone_number: Optional[str] = None
    label: Optional[str] = None
    agent_id: Optional[str] = None
    is_active: bool = True
    connected_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        session_name: str,
        label: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> WhatsAppNumber:
        now = datetime.utcnow()
        return WhatsAppNumber(
            id=uuid4(),
            tenant_id=tenant_id,
            session_name=session_name,
            label=label,
            agent_id=agent_id,
            created_at=now,
            updated_at=now,
        )
