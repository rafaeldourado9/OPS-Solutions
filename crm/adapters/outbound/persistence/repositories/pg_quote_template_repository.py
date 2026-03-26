from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.quote_template_model import QuoteTemplateModel
from core.domain.quote_template import QuoteTemplate
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort


class PgQuoteTemplateRepository(QuoteTemplateRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, template: QuoteTemplate) -> None:
        self._session.add(self._to_model(template))
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, template_id: UUID) -> Optional[QuoteTemplate]:
        stmt = select(QuoteTemplateModel).where(
            QuoteTemplateModel.id == template_id,
            QuoteTemplateModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: UUID) -> list[QuoteTemplate]:
        stmt = (
            select(QuoteTemplateModel)
            .where(QuoteTemplateModel.tenant_id == tenant_id)
            .order_by(QuoteTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, tenant_id: UUID, template_id: UUID) -> bool:
        stmt = select(QuoteTemplateModel).where(
            QuoteTemplateModel.id == template_id,
            QuoteTemplateModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    @staticmethod
    def _to_model(t: QuoteTemplate) -> QuoteTemplateModel:
        return QuoteTemplateModel(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            description=t.description,
            file_key=t.file_key,
            placeholders=t.placeholders,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )

    @staticmethod
    def _to_domain(m: QuoteTemplateModel) -> QuoteTemplate:
        return QuoteTemplate(
            id=m.id,
            tenant_id=m.tenant_id,
            name=m.name,
            description=m.description,
            file_key=m.file_key,
            placeholders=m.placeholders or [],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
