from dataclasses import dataclass, field
from uuid import UUID

from core.ports.outbound.customer_repository import CustomerRepositoryPort
from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort
from core.ports.outbound.pdf_exporter_port import PdfExporterPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.ports.outbound.storage_port import StoragePort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


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
        customer_repo: CustomerRepositoryPort | None = None,
        tenant_repo: TenantRepositoryPort | None = None,
    ) -> None:
        self._quote_repo = quote_repo
        self._template_repo = template_repo
        self._storage = storage
        self._engine = docx_engine
        self._pdf_exporter = pdf_exporter
        self._customer_repo = customer_repo
        self._tenant_repo = tenant_repo

    async def execute(self, request: GenerateQuoteDocumentRequest) -> GeneratedDocument:
        quote = await self._quote_repo.get_by_id(request.tenant_id, request.quote_id)
        if not quote:
            raise ValueError("Quote not found")

        template = await self._template_repo.get_by_id(request.tenant_id, request.template_id)
        if not template:
            raise ValueError("Template not found")

        # Download DOCX template
        docx_bytes = await self._storage.download(template.file_key)

        # Build context: company data (lowest priority) → quote data → customer data → extra
        context: dict[str, str] = {}

        # Company/tenant context (fills {nome_empresa}, {cnpj}, {pix_chave}, etc.)
        if self._tenant_repo:
            tenant = await self._tenant_repo.get_by_id(request.tenant_id)
            if tenant:
                context.update(self._build_company_context(tenant))

        # Quote data overrides company defaults
        context.update(self._build_context(quote))

        # Enrich with customer data if available
        if self._customer_repo and quote.customer_id:
            customer = await self._customer_repo.get_by_id(request.tenant_id, quote.customer_id)
            if customer:
                context.update(self._build_customer_context(customer))

        # Apply field_mapping: map template placeholder keys to CRM field values.
        # e.g. {"client_name": "nome_cliente"} → context["client_name"] = context["nome_cliente"]
        for placeholder_key, crm_field in template.field_mapping.items():
            if crm_field == "__manual__":
                # Will be filled from extra_context if provided
                continue
            if crm_field in context:
                context[placeholder_key] = context[crm_field]

        # extra_context overrides everything (manual fields + any override)
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
    def _build_company_context(tenant) -> dict[str, str]:
        """Builds template context from tenant company/banking settings."""
        # raw_settings is the full JSONB dict; settings is TenantSettings dataclass
        raw: dict = getattr(tenant, 'raw_settings', None) or {}
        company: dict = raw.get('company', {}) or {}
        banking: dict = raw.get('banking', {}) or {}

        addr_parts = [
            company.get('address_street', ''),
            company.get('address_number', ''),
            company.get('address_neighborhood', ''),
            company.get('address_city', ''),
            company.get('address_state', ''),
        ]
        address = ', '.join(p for p in addr_parts if p)

        return {
            'nome_empresa': company.get('name', '') or tenant.name or '',
            'cnpj': company.get('cnpj', ''),
            'telefone_empresa': company.get('phone', ''),
            'email_empresa': company.get('email', ''),
            'website_empresa': company.get('website', ''),
            'endereco_empresa': address,
            'cidade_empresa': company.get('address_city', ''),
            'estado_empresa': company.get('address_state', ''),
            'banco': banking.get('bank_name', ''),
            'agencia': banking.get('agency', ''),
            'conta': banking.get('account', ''),
            'tipo_conta': banking.get('account_type', ''),
            'pix_tipo': banking.get('pix_key_type', ''),
            'pix_chave': banking.get('pix_key', ''),
            'beneficiario': banking.get('beneficiary', ''),
            'logo_url': tenant.logo_url or '',
        }

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
            "notas": quote.notes or "",
            "data_criacao": fmt_date(quote.created_at),
            "data_atual": datetime.utcnow().strftime("%d/%m/%Y"),
        }

        for i, item in enumerate(quote.items, start=1):
            context[f"item_{i}_descricao"] = item.description
            context[f"item_{i}_quantidade"] = str(item.quantity)
            context[f"item_{i}_preco"] = fmt_money(item.unit_price)
            context[f"item_{i}_subtotal"] = fmt_money(item.subtotal)

        return context

    @staticmethod
    def _build_customer_context(customer) -> dict[str, str]:
        ctx: dict[str, str] = {
            "nome_cliente": customer.name or "",
            "telefone_cliente": customer.phone or "",
            "email_cliente": customer.email or "",
        }
        if customer.address:
            ctx["cidade_cliente"] = customer.address.city or ""
            ctx["estado_cliente"] = customer.address.state or ""
            addr_parts = [
                customer.address.street,
                customer.address.number,
                customer.address.complement,
                customer.address.neighborhood,
            ]
            ctx["endereco_cliente"] = ", ".join(p for p in addr_parts if p)
        else:
            ctx["cidade_cliente"] = ""
            ctx["estado_cliente"] = ""
            ctx["endereco_cliente"] = ""
        return ctx
