from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.quote_template import QuoteTemplate


class QuoteTemplateRepositoryPort(ABC):

    @abstractmethod
    async def save(self, template: QuoteTemplate) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, template_id: UUID) -> Optional[QuoteTemplate]: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[QuoteTemplate]: ...

    @abstractmethod
    async def delete(self, tenant_id: UUID, template_id: UUID) -> bool: ...

    @abstractmethod
    async def update_mapping(
        self, tenant_id: UUID, template_id: UUID, field_mapping: dict[str, str]
    ) -> Optional[QuoteTemplate]: ...
