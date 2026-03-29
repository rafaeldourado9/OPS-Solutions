from dataclasses import dataclass, field
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
    # Optional: AI-suggested injections confirmed by the user.
    # Maps original_text → placeholder_key (e.g. {"R$ 0,00": "valor_total"}).
    # When provided, the engine rewrites the DOCX inserting {placeholder} syntax
    # before extracting placeholders and saving.
    inject_suggestions: dict[str, str] = field(default_factory=dict)


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
        docx_bytes = request.docx_bytes

        # If AI suggestions were confirmed, rewrite the DOCX inserting {placeholders}
        if request.inject_suggestions:
            docx_bytes = self._engine.inject_placeholders(
                docx_bytes, request.inject_suggestions
            )

        placeholders = self._engine.extract_placeholders(docx_bytes)

        template = QuoteTemplate.create(
            tenant_id=request.tenant_id,
            name=request.name,
            file_key="",  # set below after id is known
            placeholders=placeholders,
            description=request.description,
        )
        template.file_key = f"templates/{request.tenant_id}/{template.id}.docx"

        await self._storage.upload(
            key=template.file_key,
            data=docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        await self._repo.save(template)
        return template
