from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.premise import Premise


class PremiseRepositoryPort(ABC):

    @abstractmethod
    async def save(self, premise: Premise) -> None: ...

    @abstractmethod
    async def update(self, premise: Premise) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, premise_id: UUID) -> Optional[Premise]: ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: UUID, active_only: bool = True
    ) -> list[Premise]: ...

    @abstractmethod
    async def delete(self, tenant_id: UUID, premise_id: UUID) -> bool: ...
