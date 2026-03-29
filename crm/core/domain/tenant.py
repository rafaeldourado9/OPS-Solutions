from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    trial_ends_at: Optional[datetime] = None
    settings: TenantSettings = field(default_factory=TenantSettings)
    # Active config shown in UI (may differ from agent_id which is the running agent)
    active_config_id: Optional[str] = None
    # All agent directories owned by this tenant
    owned_agents: list = field(default_factory=list)
    # Raw JSONB settings dict (company, banking, integrations, etc.)
    raw_settings: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def get_active_agent_id(self) -> str:
        """Returns the agent config to use for UI reads/writes."""
        return self.active_config_id or self.agent_id

    def get_owned_agents(self) -> list[str]:
        """Returns the list of agent IDs owned by this tenant."""
        return list(self.owned_agents)

    @property
    def is_trial_active(self) -> bool:
        if self.trial_ends_at is None:
            return True
        return datetime.utcnow() < self.trial_ends_at

    @property
    def trial_days_remaining(self) -> int:
        if self.trial_ends_at is None:
            return 999
        delta = (self.trial_ends_at - datetime.utcnow()).days
        return max(delta, 0)

    @property
    def effective_plan(self) -> str:
        """Returns 'pro' during active trial, otherwise returns the subscribed plan."""
        if self.is_trial_active and self.trial_ends_at is not None:
            return "pro"
        return self.plan

    @staticmethod
    def create(
        slug: str,
        name: str,
        agent_id: str,
        gateway_session: str = "default",
        gateway_url: str = "http://gateway:3000",
        owned_agents: Optional[list] = None,
    ) -> Tenant:
        now = datetime.utcnow()
        return Tenant(
            id=uuid4(),
            slug=slug,
            name=name,
            agent_id=agent_id,
            gateway_session=gateway_session,
            gateway_url=gateway_url,
            owned_agents=owned_agents if owned_agents is not None else [],
            trial_ends_at=now + timedelta(days=14),
            created_at=now,
            updated_at=now,
        )
