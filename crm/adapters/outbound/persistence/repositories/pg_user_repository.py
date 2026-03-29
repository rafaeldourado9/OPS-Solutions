from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.user_model import UserModel
from core.domain.user import Role, User
from core.ports.outbound.user_repository import UserRepositoryPort


class PgUserRepository(UserRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        model = UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            password_hash=user.password_hash,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self._session.get(UserModel, user_id)
        return self._to_domain(result) if result else None

    async def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        stmt = select(UserModel).where(
            UserModel.tenant_id == tenant_id,
            UserModel.email == email,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: UUID) -> list[User]:
        stmt = select(UserModel).where(UserModel.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            tenant_id=model.tenant_id,
            email=model.email,
            password_hash=model.password_hash,
            name=model.name,
            role=Role(model.role),
            is_active=model.is_active,
            avatar_url=getattr(model, 'avatar_url', None),
            created_at=model.created_at,
        )

    async def get_by_email_global(self, email: str):
        from sqlalchemy import select as sa_select
        stmt = sa_select(UserModel).where(UserModel.email == email).limit(1)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None
