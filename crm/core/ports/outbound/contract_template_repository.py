from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.contract_template import ContractTemplate


class ContractTemplateRepositoryPort(ABC):

    @abstractmethod
    async def save(self, template: ContractTemplate) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, template_id: UUID) -> Optional[ContractTemplate]: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[ContractTemplate]: ...

    @abstractmethod
    async def delete(self, tenant_id: UUID, template_id: UUID) -> bool: ...
