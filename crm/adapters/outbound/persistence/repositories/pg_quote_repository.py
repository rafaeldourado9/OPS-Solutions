from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.quote_model import QuoteModel
from core.domain.quote import AppliedPremise, Quote, QuoteItem, QuoteStatus
from core.ports.outbound.quote_repository import QuoteRepositoryPort


class PgQuoteRepository(QuoteRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, quote: Quote) -> None:
        self._session.add(self._to_model(quote))
        await self._session.flush()

    async def update(self, quote: Quote) -> None:
        stmt = (
            update(QuoteModel)
            .where(QuoteModel.id == quote.id, QuoteModel.tenant_id == quote.tenant_id)
            .values(
                customer_id=quote.customer_id,
                lead_id=quote.lead_id,
                title=quote.title,
                status=quote.status.value if isinstance(quote.status, QuoteStatus) else quote.status,
                notes=quote.notes,
                valid_until=quote.valid_until,
                currency=quote.currency,
                items_json=self._items_to_json(quote.items),
                applied_premises_json=self._premises_to_json(quote.applied_premises),
                updated_at=quote.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, quote_id: UUID) -> Optional[Quote]:
        stmt = select(QuoteModel).where(
            QuoteModel.id == quote_id, QuoteModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Quote], int]:
        base = select(QuoteModel).where(QuoteModel.tenant_id == tenant_id)
        if status:
            base = base.where(QuoteModel.status == status)
        if customer_id:
            base = base.where(QuoteModel.customer_id == customer_id)
        if lead_id:
            base = base.where(QuoteModel.lead_id == lead_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        query = base.order_by(QuoteModel.updated_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = [self._to_domain(m) for m in result.scalars().all()]
        return items, total

    async def delete(self, tenant_id: UUID, quote_id: UUID) -> bool:
        stmt = select(QuoteModel).where(
            QuoteModel.id == quote_id, QuoteModel.tenant_id == tenant_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    @staticmethod
    def _items_to_json(items: list[QuoteItem]) -> list[dict]:
        return [
            {
                "id": str(item.id),
                "quote_id": str(item.quote_id),
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount": item.discount,
                "notes": item.notes,
            }
            for item in items
        ]

    @staticmethod
    def _premises_to_json(premises: list[AppliedPremise]) -> list[dict]:
        return [
            {
                "premise_id": str(ap.premise_id),
                "name": ap.name,
                "type": ap.type,
                "value": ap.value,
                "amount": ap.amount,
            }
            for ap in premises
        ]

    @classmethod
    def _to_model(cls, q: Quote) -> QuoteModel:
        return QuoteModel(
            id=q.id,
            tenant_id=q.tenant_id,
            customer_id=q.customer_id,
            lead_id=q.lead_id,
            title=q.title,
            status=q.status.value if isinstance(q.status, QuoteStatus) else q.status,
            notes=q.notes,
            valid_until=q.valid_until,
            currency=q.currency,
            items_json=cls._items_to_json(q.items),
            applied_premises_json=cls._premises_to_json(q.applied_premises),
            created_at=q.created_at,
            updated_at=q.updated_at,
        )

    @staticmethod
    def _to_domain(m: QuoteModel) -> Quote:
        from uuid import UUID as _UUID

        items = [
            QuoteItem(
                id=_UUID(d["id"]),
                quote_id=_UUID(d["quote_id"]),
                description=d["description"],
                quantity=d["quantity"],
                unit_price=d["unit_price"],
                discount=d.get("discount", 0.0),
                notes=d.get("notes", ""),
            )
            for d in (m.items_json or [])
        ]
        applied_premises = [
            AppliedPremise(
                premise_id=_UUID(d["premise_id"]),
                name=d["name"],
                type=d["type"],
                value=d["value"],
                amount=d["amount"],
            )
            for d in (m.applied_premises_json or [])
        ]
        return Quote(
            id=m.id,
            tenant_id=m.tenant_id,
            customer_id=m.customer_id,
            lead_id=m.lead_id,
            title=m.title,
            status=QuoteStatus(m.status),
            items=items,
            applied_premises=applied_premises,
            notes=m.notes,
            valid_until=m.valid_until,
            currency=m.currency,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
