from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.user import User


class UserRepositoryPort(ABC):

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...

    @abstractmethod
    async def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[User]: ...
