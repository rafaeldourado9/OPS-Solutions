from uuid import UUID

from core.domain.quote_template import QuoteTemplate
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort


class ListQuoteTemplatesUseCase:

    def __init__(self, template_repo: QuoteTemplateRepositoryPort) -> None:
        self._repo = template_repo

    async def execute(self, tenant_id: UUID) -> list[QuoteTemplate]:
        return await self._repo.list_by_tenant(tenant_id)
