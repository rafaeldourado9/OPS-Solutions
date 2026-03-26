from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.contract_model import ContractModel
from core.domain.contract import Contract, ContractStatus
from core.ports.outbound.contract_repository import ContractRepositoryPort


class PgContractRepository(ContractRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, contract: Contract) -> None:
        self._session.add(self._to_model(contract))
        await self._session.flush()

    async def update(self, contract: Contract) -> None:
        stmt = (
            update(ContractModel)
            .where(ContractModel.id == contract.id, ContractModel.tenant_id == contract.tenant_id)
            .values(
                title=contract.title,
                status=contract.status.value if isinstance(contract.status, ContractStatus) else contract.status,
                content=contract.content,
                signed_at=contract.signed_at,
                expires_at=contract.expires_at,
                updated_at=contract.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, contract_id: UUID) -> Optional[Contract]:
        stmt = select(ContractModel).where(
            ContractModel.id == contract_id, ContractModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_quote_id(self, tenant_id: UUID, quote_id: UUID) -> Optional[Contract]:
        stmt = select(ContractModel).where(
            ContractModel.quote_id == quote_id, ContractModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Contract], int]:
        base = select(ContractModel).where(ContractModel.tenant_id == tenant_id)
        if status:
            base = base.where(ContractModel.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        query = base.order_by(ContractModel.updated_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()], total

    @staticmethod
    def _to_model(c: Contract) -> ContractModel:
        return ContractModel(
            id=c.id,
            tenant_id=c.tenant_id,
            quote_id=c.quote_id,
            customer_id=c.customer_id,
            title=c.title,
            status=c.status.value if isinstance(c.status, ContractStatus) else c.status,
            content=c.content,
            signed_at=c.signed_at,
            expires_at=c.expires_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    @staticmethod
    def _to_domain(m: ContractModel) -> Contract:
        return Contract(
            id=m.id,
            tenant_id=m.tenant_id,
            quote_id=m.quote_id,
            customer_id=m.customer_id,
            title=m.title,
            status=ContractStatus(m.status),
            content=m.content,
            signed_at=m.signed_at,
            expires_at=m.expires_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
