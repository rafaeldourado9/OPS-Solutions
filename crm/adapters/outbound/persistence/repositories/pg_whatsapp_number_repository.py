from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.whatsapp_number_model import WhatsAppNumberModel
from core.domain.whatsapp_number import WhatsAppNumber


class PgWhatsAppNumberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, m: WhatsAppNumberModel) -> WhatsAppNumber:
        return WhatsAppNumber(
            id=m.id,
            tenant_id=m.tenant_id,
            session_name=m.session_name,
            phone_number=m.phone_number,
            label=m.label,
            agent_id=m.agent_id,
            is_active=m.is_active,
            connected_at=m.connected_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_by_tenant(self, tenant_id: UUID) -> list[WhatsAppNumber]:
        result = await self._session.execute(
            select(WhatsAppNumberModel)
            .where(WhatsAppNumberModel.tenant_id == tenant_id)
            .order_by(WhatsAppNumberModel.created_at)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_id(self, number_id: UUID) -> Optional[WhatsAppNumber]:
        result = await self._session.execute(
            select(WhatsAppNumberModel).where(WhatsAppNumberModel.id == number_id)
        )
        m = result.scalar_one_or_none()
        return self._to_domain(m) if m else None

    async def get_by_session(self, session_name: str) -> Optional[WhatsAppNumber]:
        result = await self._session.execute(
            select(WhatsAppNumberModel).where(WhatsAppNumberModel.session_name == session_name)
        )
        m = result.scalar_one_or_none()
        return self._to_domain(m) if m else None

    async def save(self, number: WhatsAppNumber) -> None:
        model = WhatsAppNumberModel(
            id=number.id,
            tenant_id=number.tenant_id,
            session_name=number.session_name,
            phone_number=number.phone_number,
            label=number.label,
            agent_id=number.agent_id,
            is_active=number.is_active,
            connected_at=number.connected_at,
            created_at=number.created_at,
            updated_at=number.updated_at,
        )
        self._session.add(model)
        await self._session.commit()

    async def update(self, number: WhatsAppNumber) -> None:
        result = await self._session.execute(
            select(WhatsAppNumberModel).where(WhatsAppNumberModel.id == number.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return
        model.phone_number = number.phone_number
        model.label = number.label
        model.agent_id = number.agent_id
        model.is_active = number.is_active
        model.connected_at = number.connected_at
        await self._session.commit()

    async def delete(self, number_id: UUID) -> None:
        result = await self._session.execute(
            select(WhatsAppNumberModel).where(WhatsAppNumberModel.id == number_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        result = await self._session.execute(
            select(WhatsAppNumberModel).where(WhatsAppNumberModel.tenant_id == tenant_id)
        )
        return len(result.scalars().all())
