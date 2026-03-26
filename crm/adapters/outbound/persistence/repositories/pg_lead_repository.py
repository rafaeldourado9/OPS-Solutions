from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.lead_model import LeadModel
from core.domain.lead import Lead, LeadStage
from core.ports.outbound.lead_repository import LeadRepositoryPort


class PgLeadRepository(LeadRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, lead: Lead) -> None:
        model = self._to_model(lead)
        self._session.add(model)
        await self._session.flush()

    async def update(self, lead: Lead) -> None:
        stmt = (
            update(LeadModel)
            .where(LeadModel.id == lead.id, LeadModel.tenant_id == lead.tenant_id)
            .values(
                customer_id=lead.customer_id,
                title=lead.title,
                stage=lead.stage.value if isinstance(lead.stage, LeadStage) else lead.stage,
                value=lead.value,
                currency=lead.currency,
                source=lead.source,
                assigned_to=lead.assigned_to,
                notes=lead.notes,
                expected_close_date=lead.expected_close_date,
                closed_at=lead.closed_at,
                lost_reason=lead.lost_reason,
                tags=lead.tags,
                updated_at=lead.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, lead_id: UUID) -> Optional[Lead]:
        stmt = select(LeadModel).where(
            LeadModel.id == lead_id, LeadModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        stage: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Lead], int]:
        base = select(LeadModel).where(LeadModel.tenant_id == tenant_id)

        if stage:
            base = base.where(LeadModel.stage == stage)
        if assigned_to:
            base = base.where(LeadModel.assigned_to == assigned_to)
        if search:
            base = base.where(LeadModel.title.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        query = base.order_by(LeadModel.updated_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = [self._to_domain(m) for m in result.scalars().all()]

        return items, total

    async def delete(self, tenant_id: UUID, lead_id: UUID) -> bool:
        lead = await self.get_by_id(tenant_id, lead_id)
        if not lead:
            return False
        stmt = select(LeadModel).where(
            LeadModel.id == lead_id, LeadModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    @staticmethod
    def _to_model(lead: Lead) -> LeadModel:
        return LeadModel(
            id=lead.id,
            tenant_id=lead.tenant_id,
            customer_id=lead.customer_id,
            title=lead.title,
            stage=lead.stage.value if isinstance(lead.stage, LeadStage) else lead.stage,
            value=lead.value,
            currency=lead.currency,
            source=lead.source,
            assigned_to=lead.assigned_to,
            notes=lead.notes,
            expected_close_date=lead.expected_close_date,
            closed_at=lead.closed_at,
            lost_reason=lead.lost_reason,
            tags=lead.tags,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )

    @staticmethod
    def _to_domain(m: LeadModel) -> Lead:
        return Lead(
            id=m.id,
            tenant_id=m.tenant_id,
            customer_id=m.customer_id,
            title=m.title,
            stage=LeadStage(m.stage),
            value=m.value,
            currency=m.currency,
            source=m.source,
            assigned_to=m.assigned_to,
            notes=m.notes,
            expected_close_date=m.expected_close_date,
            closed_at=m.closed_at,
            lost_reason=m.lost_reason,
            tags=m.tags or [],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
