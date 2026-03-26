from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.contract import Contract


class ContractRepositoryPort(ABC):

    @abstractmethod
    async def save(self, contract: Contract) -> None: ...

    @abstractmethod
    async def update(self, contract: Contract) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, contract_id: UUID) -> Optional[Contract]: ...

    @abstractmethod
    async def get_by_quote_id(self, tenant_id: UUID, quote_id: UUID) -> Optional[Contract]: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Contract], int]: ...
