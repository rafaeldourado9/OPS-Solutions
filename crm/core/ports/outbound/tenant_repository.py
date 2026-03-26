from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.tenant import Tenant


class TenantRepositoryPort(ABC):

    @abstractmethod
    async def save(self, tenant: Tenant) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Tenant]: ...

    @abstractmethod
    async def get_by_agent_id(self, agent_id: str) -> Optional[Tenant]: ...

    @abstractmethod
    async def get_by_gateway_session(self, gateway_session: str) -> Optional[Tenant]: ...

    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool: ...
