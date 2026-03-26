from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.customer_model import CustomerModel
from core.domain.customer import Address, Customer
from core.ports.outbound.customer_repository import CustomerRepositoryPort


class PgCustomerRepository(CustomerRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, customer: Customer) -> None:
        model = self._to_model(customer)
        self._session.add(model)
        await self._session.flush()

    async def update(self, customer: Customer) -> None:
        stmt = (
            update(CustomerModel)
            .where(
                CustomerModel.id == customer.id,
                CustomerModel.tenant_id == customer.tenant_id,
            )
            .values(
                name=customer.name,
                email=customer.email,
                cpf_cnpj=customer.cpf_cnpj,
                company_name=customer.company_name,
                address=self._address_to_dict(customer.address) if customer.address else None,
                tags=customer.tags,
                notes=customer.notes,
                is_active=customer.is_active,
                updated_at=customer.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID, customer_id: UUID) -> Optional[Customer]:
        stmt = select(CustomerModel).where(
            CustomerModel.id == customer_id,
            CustomerModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_phone(self, tenant_id: UUID, phone: str) -> Optional[Customer]:
        stmt = select(CustomerModel).where(
            CustomerModel.tenant_id == tenant_id,
            CustomerModel.phone == phone,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[Customer]:
        stmt = select(CustomerModel).where(
            CustomerModel.tenant_id == tenant_id,
            CustomerModel.chat_id == chat_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> tuple[list[Customer], int]:
        base = select(CustomerModel).where(
            CustomerModel.tenant_id == tenant_id,
            CustomerModel.is_active == True,  # noqa: E712
        )

        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    CustomerModel.name.ilike(pattern),
                    CustomerModel.phone.ilike(pattern),
                    CustomerModel.email.ilike(pattern),
                    CustomerModel.company_name.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        query = base.order_by(CustomerModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = [self._to_domain(m) for m in result.scalars().all()]

        return items, total

    async def delete(self, tenant_id: UUID, customer_id: UUID) -> bool:
        stmt = (
            update(CustomerModel)
            .where(CustomerModel.id == customer_id, CustomerModel.tenant_id == tenant_id)
            .values(is_active=False)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    @staticmethod
    def _to_model(customer: Customer) -> CustomerModel:
        return CustomerModel(
            id=customer.id,
            tenant_id=customer.tenant_id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            cpf_cnpj=customer.cpf_cnpj,
            company_name=customer.company_name,
            address=PgCustomerRepository._address_to_dict(customer.address),
            tags=customer.tags,
            notes=customer.notes,
            source=customer.source,
            chat_id=customer.chat_id,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )

    @staticmethod
    def _address_to_dict(address: Optional[Address]) -> Optional[dict]:
        if not address:
            return None
        return {
            "street": address.street,
            "number": address.number,
            "complement": address.complement,
            "neighborhood": address.neighborhood,
            "city": address.city,
            "state": address.state,
            "zip_code": address.zip_code,
        }

    @staticmethod
    def _to_domain(model: CustomerModel) -> Customer:
        address = None
        if model.address:
            address = Address(**model.address)

        return Customer(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            phone=model.phone,
            email=model.email,
            cpf_cnpj=model.cpf_cnpj,
            company_name=model.company_name,
            address=address,
            tags=model.tags or [],
            notes=model.notes or "",
            source=model.source,
            chat_id=model.chat_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
