from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.tenant_model import TenantModel
from core.domain.tenant import Tenant, TenantSettings
from core.ports.outbound.tenant_repository import TenantRepositoryPort


class PgTenantRepository(TenantRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tenant: Tenant) -> None:
        model = TenantModel(
            id=tenant.id,
            slug=tenant.slug,
            name=tenant.name,
            logo_url=tenant.logo_url,
            primary_color=tenant.primary_color,
            secondary_color=tenant.secondary_color,
            agent_id=tenant.agent_id,
            gateway_session=tenant.gateway_session,
            gateway_url=tenant.gateway_url,
            plan=tenant.plan,
            is_active=tenant.is_active,
            trial_ends_at=tenant.trial_ends_at,
            settings={
                **tenant.raw_settings,  # preserve company, banking, integrations, etc.
                "timezone": tenant.settings.timezone,
                "currency": tenant.settings.currency,
                "locale": tenant.settings.locale,
                "owned_agents": tenant.owned_agents,
                "active_config_id": tenant.active_config_id,
            },
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        result = await self._session.get(TenantModel, tenant_id)
        return self._to_domain(result) if result else None

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        stmt = select(TenantModel).where(TenantModel.slug == slug)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_agent_id(self, agent_id: str) -> Optional[Tenant]:
        stmt = select(TenantModel).where(TenantModel.agent_id == agent_id).limit(1)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def get_by_gateway_session(self, gateway_session: str) -> Optional[Tenant]:
        stmt = select(TenantModel).where(TenantModel.gateway_session == gateway_session).limit(1)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def get_by_owned_agent_id(self, agent_id: str) -> Optional[Tenant]:
        """Find a tenant that owns this agent_id (stored in settings.owned_agents JSON array).
        Uses JSONB containment operator to avoid substring false-positives."""
        import json
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        stmt = select(TenantModel).where(
            TenantModel.settings["owned_agents"].contains(
                cast(json.dumps([agent_id]), JSONB)
            )
        ).limit(1)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def exists_by_slug(self, slug: str) -> bool:
        stmt = select(TenantModel.id).where(TenantModel.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_domain(model: TenantModel) -> Tenant:
        s = model.settings or {}
        return Tenant(
            id=model.id,
            slug=model.slug,
            name=model.name,
            logo_url=model.logo_url,
            primary_color=model.primary_color,
            secondary_color=model.secondary_color,
            agent_id=model.agent_id,
            gateway_session=model.gateway_session,
            gateway_url=model.gateway_url,
            plan=model.plan,
            is_active=model.is_active,
            trial_ends_at=model.trial_ends_at,
            settings=TenantSettings(
                timezone=s.get("timezone", "America/Sao_Paulo"),
                currency=s.get("currency", "BRL"),
                locale=s.get("locale", "pt-BR"),
            ),
            active_config_id=s.get("active_config_id"),
            owned_agents=s.get("owned_agents", []),
            raw_settings=s,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
