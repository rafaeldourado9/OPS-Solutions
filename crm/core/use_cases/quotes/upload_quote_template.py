from dataclasses import dataclass
from uuid import UUID

from core.domain.quote_template import QuoteTemplate
from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.ports.outbound.storage_port import StoragePort


@dataclass(frozen=True)
class UploadQuoteTemplateRequest:
    tenant_id: UUID
    name: str
    docx_bytes: bytes
    description: str = ""


class UploadQuoteTemplateUseCase:

    def __init__(
        self,
        template_repo: QuoteTemplateRepositoryPort,
        storage: StoragePort,
        docx_engine: DocxTemplateEnginePort,
    ) -> None:
        self._repo = template_repo
        self._storage = storage
        self._engine = docx_engine

    async def execute(self, request: UploadQuoteTemplateRequest) -> QuoteTemplate:
        placeholders = self._engine.extract_placeholders(request.docx_bytes)

        template = QuoteTemplate.create(
            tenant_id=request.tenant_id,
            name=request.name,
            file_key=f"templates/{request.tenant_id}/{request.name.replace(' ', '_')}.docx",
            placeholders=placeholders,
            description=request.description,
        )
        # Use id to guarantee unique key
        template.file_key = f"templates/{request.tenant_id}/{template.id}.docx"

        await self._storage.upload(
            key=template.file_key,
            data=request.docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        await self._repo.save(template)
        return template
