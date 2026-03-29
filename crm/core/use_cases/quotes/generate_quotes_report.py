from __future__ import annotations

import io
from datetime import datetime
from typing import Optional
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)

from core.domain.quote import Quote
from core.domain.tenant import Tenant
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


ACCENT = colors.HexColor("#0ABAB5")
HEADER_BG = colors.HexColor("#F4F4F5")
BORDER_COLOR = colors.HexColor("#E4E4E7")

STATUS_LABEL = {
    "draft": "Rascunho",
    "sent": "Enviado",
    "approved": "Aprovado",
    "rejected": "Rejeitado",
    "expired": "Expirado",
}


class GenerateQuotesReportUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        quote_repo: QuoteRepositoryPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._quote_repo = quote_repo

    async def execute(
        self,
        tenant_id: UUID,
        customer_names: dict[UUID, str] | None = None,
    ) -> bytes:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        result = await self._quote_repo.list_by_tenant(
            tenant_id, offset=0, limit=1000
        )
        quotes = result.items

        return self._build_pdf(tenant, quotes, customer_names or {})

    def _build_pdf(
        self,
        tenant: Tenant,
        quotes: list[Quote],
        customer_names: dict[UUID, str],
    ) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1D1D1F"),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#71717A"),
            spaceAfter=2,
        )
        section_style = ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#1D1D1F"),
            spaceBefore=12,
            spaceAfter=6,
        )

        elements = []
        now = datetime.now()

        # ── Header ──
        elements.append(Paragraph(tenant.name, title_style))
        elements.append(Paragraph(
            f"Relatório de Orçamentos — Gerado em {now.strftime('%d/%m/%Y às %H:%M')}",
            subtitle_style,
        ))
        elements.append(Spacer(1, 4 * mm))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=ACCENT, spaceAfter=6 * mm
        ))

        # ── Summary ──
        total_quotes = len(quotes)
        aprovados = sum(1 for q in quotes if self._status_val(q) == "approved")
        enviados = sum(1 for q in quotes if self._status_val(q) == "sent")
        rascunhos = sum(1 for q in quotes if self._status_val(q) == "draft")
        rejeitados = sum(1 for q in quotes if self._status_val(q) == "rejected")
        receita_potencial = sum(
            q.total for q in quotes if self._status_val(q) != "rejected"
        )
        receita_aprovada = sum(
            q.total for q in quotes if self._status_val(q) == "approved"
        )

        summary_data = [
            ["Total de Orçamentos", str(total_quotes)],
            ["Aprovados", str(aprovados)],
            ["Enviados / Aguardando", str(enviados)],
            ["Rascunhos", str(rascunhos)],
            ["Rejeitados", str(rejeitados)],
            ["Receita Potencial", self._fmt_currency(receita_potencial)],
            ["Receita Aprovada", self._fmt_currency(receita_aprovada)],
        ]
        summary_table = Table(summary_data, colWidths=[120 * mm, 50 * mm])
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#71717A")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1D1D1F")),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 6 * mm))

        # ── Quotes Table ──
        elements.append(Paragraph("Orçamentos", section_style))

        header = ["Cliente", "Descrição", "Data", "Valor", "Status"]
        rows = [header]
        for q in sorted(quotes, key=lambda x: x.created_at, reverse=True):
            cname = customer_names.get(q.customer_id, "—") if q.customer_id else "—"
            status = STATUS_LABEL.get(self._status_val(q), self._status_val(q))
            rows.append([
                cname,
                q.title,
                q.created_at.strftime("%d/%m/%Y"),
                self._fmt_currency(q.total),
                status,
            ])

        col_widths = [45 * mm, 55 * mm, 25 * mm, 28 * mm, 27 * mm]
        quote_table = Table(rows, colWidths=col_widths, repeatRows=1)
        quote_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#71717A")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#3F3F46")),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER_COLOR),
            ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#F4F4F5")),
            ("LINEBELOW", (0, -1), (-1, -1), 1, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(quote_table)

        # ── Footer ──
        elements.append(Spacer(1, 10 * mm))
        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=3 * mm
        ))
        elements.append(Paragraph(
            f"{tenant.name} — Relatório gerado automaticamente em {now.strftime('%d/%m/%Y %H:%M')}",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#A1A1AA")),
        ))

        doc.build(elements)
        return buf.getvalue()

    @staticmethod
    def _status_val(q: Quote) -> str:
        return q.status.value if hasattr(q.status, "value") else q.status

    @staticmethod
    def _fmt_currency(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
