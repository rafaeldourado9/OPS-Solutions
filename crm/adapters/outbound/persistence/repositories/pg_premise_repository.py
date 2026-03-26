from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.premise_model import PremiseModel
from core.domain.premise import Premise, PremiseType
from core.ports.outbound.premise_repository import PremiseRepositoryPort


class PgPremiseRepository(PremiseRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, premise: Premise) -> None:
        self._session.add(self._to_model(premise))
        await self._session.flush()

    async def update(self, premise: Premise) -> None:
        stmt = (
            update(PremiseModel)
            .where(PremiseModel.id == premise.id, PremiseModel.tenant_id == premise.tenant_id)
            .values(
                name=premise.name,
                type=premise.type.value if isinstance(premise.type, PremiseType) else premise.type,
                value=premise.value,
                description=premise.description,
                is_active=premise.is_active,
                updated_at=premise.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, premise_id: UUID) -> Optional[Premise]:
        stmt = select(PremiseModel).where(
            PremiseModel.id == premise_id, PremiseModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self, tenant_id: UUID, active_only: bool = True
    ) -> list[Premise]:
        stmt = select(PremiseModel).where(PremiseModel.tenant_id == tenant_id)
        if active_only:
            stmt = stmt.where(PremiseModel.is_active == True)  # noqa: E712
        stmt = stmt.order_by(PremiseModel.name)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, tenant_id: UUID, premise_id: UUID) -> bool:
        premise = await self.get_by_id(tenant_id, premise_id)
        if not premise:
            return False
        stmt = select(PremiseModel).where(
            PremiseModel.id == premise_id, PremiseModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    @staticmethod
    def _to_model(p: Premise) -> PremiseModel:
        return PremiseModel(
            id=p.id,
            tenant_id=p.tenant_id,
            name=p.name,
            type=p.type.value if isinstance(p.type, PremiseType) else p.type,
            value=p.value,
            description=p.description,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @staticmethod
    def _to_domain(m: PremiseModel) -> Premise:
        return Premise(
            id=m.id,
            tenant_id=m.tenant_id,
            name=m.name,
            type=PremiseType(m.type),
            value=m.value,
            description=m.description,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
