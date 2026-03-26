from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TenantSettings:
    timezone: str = "America/Sao_Paulo"
    currency: str = "BRL"
    locale: str = "pt-BR"


@dataclass
class Tenant:
    id: UUID
    slug: str
    name: str
    agent_id: str
    gateway_session: str
    gateway_url: str = "http://gateway:3000"
    logo_url: Optional[str] = None
    primary_color: str = "#1a73e8"
    secondary_color: str = "#ffffff"
    plan: str = "starter"
    is_active: bool = True
    settings: TenantSettings = field(default_factory=TenantSettings)
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        slug: str,
        name: str,
        agent_id: str,
        gateway_session: str = "default",
        gateway_url: str = "http://gateway:3000",
    ) -> Tenant:
        now = datetime.utcnow()
        return Tenant(
            id=uuid4(),
            slug=slug,
            name=name,
            agent_id=agent_id,
            gateway_session=gateway_session,
            gateway_url=gateway_url,
            created_at=now,
            updated_at=now,
        )
