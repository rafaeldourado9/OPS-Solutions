from dataclasses import dataclass, field
from uuid import UUID

from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort
from core.ports.outbound.pdf_exporter_port import PdfExporterPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.ports.outbound.storage_port import StoragePort


@dataclass(frozen=True)
class GenerateQuoteDocumentRequest:
    tenant_id: UUID
    quote_id: UUID
    template_id: UUID
    extra_context: dict[str, str] = field(default_factory=dict)


@dataclass
class GeneratedDocument:
    quote_id: UUID
    template_id: UUID
    pdf_key: str
    pdf_url: str
    docx_key: str
    docx_url: str


class GenerateQuoteDocumentUseCase:

    def __init__(
        self,
        quote_repo: QuoteRepositoryPort,
        template_repo: QuoteTemplateRepositoryPort,
        storage: StoragePort,
        docx_engine: DocxTemplateEnginePort,
        pdf_exporter: PdfExporterPort,
    ) -> None:
        self._quote_repo = quote_repo
        self._template_repo = template_repo
        self._storage = storage
        self._engine = docx_engine
        self._pdf_exporter = pdf_exporter

    async def execute(self, request: GenerateQuoteDocumentRequest) -> GeneratedDocument:
        quote = await self._quote_repo.get_by_id(request.tenant_id, request.quote_id)
        if not quote:
            raise ValueError("Quote not found")

        template = await self._template_repo.get_by_id(request.tenant_id, request.template_id)
        if not template:
            raise ValueError("Template not found")

        # Download DOCX template
        docx_bytes = await self._storage.download(template.file_key)

        # Build context from quote data
        context = self._build_context(quote)
        context.update(request.extra_context)

        # Fill placeholders
        filled_docx = self._engine.fill_template(docx_bytes, context)

        # Convert to PDF
        pdf_bytes = await self._pdf_exporter.convert(filled_docx)

        # Store generated files
        base_key = f"generated/{request.tenant_id}/{request.quote_id}"
        docx_key = f"{base_key}.docx"
        pdf_key = f"{base_key}.pdf"

        await self._storage.upload(
            key=docx_key,
            data=filled_docx,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        await self._storage.upload(
            key=pdf_key,
            data=pdf_bytes,
            content_type="application/pdf",
        )

        docx_url = await self._storage.get_url(docx_key)
        pdf_url = await self._storage.get_url(pdf_key)

        return GeneratedDocument(
            quote_id=request.quote_id,
            template_id=request.template_id,
            pdf_key=pdf_key,
            pdf_url=pdf_url,
            docx_key=docx_key,
            docx_url=docx_url,
        )

    @staticmethod
    def _build_context(quote) -> dict[str, str]:
        """Builds standard placeholder context from a Quote domain object."""
        from datetime import datetime

        def fmt_money(v: float) -> str:
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def fmt_date(d) -> str:
            if d is None:
                return ""
            return d.strftime("%d/%m/%Y")

        context: dict[str, str] = {
            "titulo": quote.title,
            "status": quote.status.value if hasattr(quote.status, "value") else str(quote.status),
            "total": fmt_money(quote.total),
            "itens_total": fmt_money(quote.items_total),
            "premissas_total": fmt_money(quote.premises_total),
            "moeda": quote.currency,
            "validade": fmt_date(quote.valid_until),
            "notas": quote.notes,
            "data_criacao": fmt_date(quote.created_at),
            "data_atual": datetime.utcnow().strftime("%d/%m/%Y"),
        }

        # Add per-item placeholders (item_1_desc, item_1_qty, etc.)
        for i, item in enumerate(quote.items, start=1):
            context[f"item_{i}_descricao"] = item.description
            context[f"item_{i}_quantidade"] = str(item.quantity)
            context[f"item_{i}_preco"] = fmt_money(item.unit_price)
            context[f"item_{i}_subtotal"] = fmt_money(item.subtotal)

        return context
