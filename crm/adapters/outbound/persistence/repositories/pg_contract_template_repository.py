from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.contract_template_model import ContractTemplateModel
from core.domain.contract_template import ContractTemplate
from core.ports.outbound.contract_template_repository import ContractTemplateRepositoryPort


class PgContractTemplateRepository(ContractTemplateRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, template: ContractTemplate) -> None:
        self._session.add(self._to_model(template))
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, template_id: UUID) -> Optional[ContractTemplate]:
        stmt = select(ContractTemplateModel).where(
            ContractTemplateModel.id == template_id,
            ContractTemplateModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: UUID) -> list[ContractTemplate]:
        stmt = (
            select(ContractTemplateModel)
            .where(ContractTemplateModel.tenant_id == tenant_id)
            .order_by(ContractTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, tenant_id: UUID, template_id: UUID) -> bool:
        stmt = select(ContractTemplateModel).where(
            ContractTemplateModel.id == template_id,
            ContractTemplateModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    @staticmethod
    def _to_model(t: ContractTemplate) -> ContractTemplateModel:
        return ContractTemplateModel(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            description=t.description,
            file_key=t.file_key,
            variables_json=t.variables,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )

    @staticmethod
    def _to_domain(m: ContractTemplateModel) -> ContractTemplate:
        return ContractTemplate(
            id=m.id,
            tenant_id=m.tenant_id,
            name=m.name,
            description=m.description or "",
            file_key=m.file_key,
            variables=m.variables_json or [],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
