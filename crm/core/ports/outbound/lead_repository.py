from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.lead import Lead


class LeadRepositoryPort(ABC):

    @abstractmethod
    async def save(self, lead: Lead) -> None: ...

    @abstractmethod
    async def update(self, lead: Lead) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, lead_id: UUID) -> Optional[Lead]: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        stage: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Lead], int]: ...

    @abstractmethod
    async def delete(self, tenant_id: UUID, lead_id: UUID) -> bool: ...
