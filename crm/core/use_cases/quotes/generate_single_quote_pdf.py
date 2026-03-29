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
    Image,
)

from core.domain.quote import Quote
from core.domain.tenant import Tenant
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


ACCENT = colors.HexColor("#0ABAB5")
HEADER_BG = colors.HexColor("#F4F4F5")
BORDER_COLOR = colors.HexColor("#E4E4E7")
TOTAL_BG = colors.HexColor("#F0FEFE")


class GenerateSingleQuotePdfUseCase:

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
        quote_id: UUID,
        customer_name: Optional[str] = None,
    ) -> bytes:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        quote = await self._quote_repo.get_by_id(tenant_id, quote_id)
        if not quote:
            raise ValueError("Quote not found")

        return self._build_pdf(tenant, quote, customer_name)

    def _build_pdf(
        self,
        tenant: Tenant,
        quote: Quote,
        customer_name: Optional[str],
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
            "PropTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1D1D1F"),
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "PropSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#71717A"),
            spaceAfter=2,
        )
        section_style = ParagraphStyle(
            "PropSection",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#1D1D1F"),
            spaceBefore=10,
            spaceAfter=5,
            fontName="Helvetica-Bold",
        )
        body_style = ParagraphStyle(
            "PropBody",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#3F3F46"),
        )
        label_style = ParagraphStyle(
            "PropLabel",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#71717A"),
        )
        footer_style = ParagraphStyle(
            "PropFooter",
            parent=styles["Normal"],
            fontSize=7,
            textColor=colors.HexColor("#A1A1AA"),
        )
        total_label_style = ParagraphStyle(
            "TotalLabel",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#0ABAB5"),
            fontName="Helvetica-Bold",
        )
        total_value_style = ParagraphStyle(
            "TotalValue",
            parent=styles["Normal"],
            fontSize=18,
            textColor=colors.HexColor("#0ABAB5"),
            fontName="Helvetica-Bold",
            alignment=2,  # right
        )

        elements = []
        now = datetime.now()

        # ── Header: logo or tenant name ──
        logo_added = False
        if tenant.logo_url:
            try:
                import httpx
                resp = httpx.get(tenant.logo_url, timeout=5.0, follow_redirects=True)
                if resp.status_code == 200:
                    logo_buf = io.BytesIO(resp.content)
                    logo_img = Image(logo_buf, width=40 * mm, height=15 * mm)
                    logo_img.hAlign = "LEFT"
                    elements.append(logo_img)
                    elements.append(Spacer(1, 2 * mm))
                    logo_added = True
            except Exception:
                pass

        if not logo_added:
            elements.append(Paragraph(tenant.name, title_style))
        else:
            elements.append(Paragraph(tenant.name, subtitle_style))

        elements.append(Spacer(1, 3 * mm))
        elements.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=6 * mm))

        # ── Proposta Comercial section ──
        elements.append(Paragraph("Proposta Comercial", section_style))
        elements.append(Spacer(1, 2 * mm))

        info_data = [
            [Paragraph("<b>Título:</b>", body_style), Paragraph(quote.title, body_style)],
            [Paragraph("<b>Cliente:</b>", body_style), Paragraph(customer_name or "—", body_style)],
            [Paragraph("<b>Data:</b>", body_style), Paragraph(quote.created_at.strftime("%d/%m/%Y"), body_style)],
        ]
        if quote.valid_until:
            info_data.append([
                Paragraph("<b>Válido até:</b>", body_style),
                Paragraph(quote.valid_until.strftime("%d/%m/%Y"), body_style),
            ])

        info_table = Table(info_data, colWidths=[35 * mm, 140 * mm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 6 * mm))

        # ── Items Table ──
        elements.append(Paragraph("Itens do Orçamento", section_style))

        header = ["Descrição", "Qtd", "Valor Unit.", "Subtotal"]
        rows = [header]
        for item in quote.items:
            rows.append([
                item.description,
                str(int(item.quantity)) if item.quantity == int(item.quantity) else f"{item.quantity:.2f}",
                self._fmt_currency(item.unit_price),
                self._fmt_currency(item.subtotal),
            ])

        col_widths = [100 * mm, 20 * mm, 35 * mm, 35 * mm]
        items_table = Table(rows, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#71717A")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#3F3F46")),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (3, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER_COLOR),
            ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#F4F4F5")),
            ("LINEBELOW", (0, -1), (-1, -1), 1, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 4 * mm))

        # ── Applied Premises Breakdown (if any) ──
        if quote.applied_premises:
            elements.append(Paragraph("Composição de Preço", section_style))

            prem_header = ["Premissa", "Tipo", "%", "Valor"]
            prem_rows = [prem_header]
            for ap in quote.applied_premises:
                type_label = {"percentage": "Porcentagem", "fixed": "Fixo", "multiplier": "Multiplicador"}.get(ap.type, ap.type)
                pct_str = f"{ap.value:.1f}%" if ap.type == "percentage" else "—"
                prem_rows.append([ap.name, type_label, pct_str, self._fmt_currency(ap.amount)])

            prem_col_widths = [80 * mm, 40 * mm, 30 * mm, 40 * mm]
            prem_table = Table(prem_rows, colWidths=prem_col_widths, repeatRows=1)
            prem_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#71717A")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#3F3F46")),
                ("ALIGN", (2, 0), (3, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER_COLOR),
                ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#F4F4F5")),
                ("LINEBELOW", (0, -1), (-1, -1), 1, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(prem_table)
            elements.append(Spacer(1, 4 * mm))

        # ── Total Box ──
        elements.append(Spacer(1, 4 * mm))
        total_data = [
            [Paragraph("VALOR TOTAL", total_label_style), Paragraph(self._fmt_currency(quote.total), total_value_style)],
        ]
        total_table = Table(total_data, colWidths=[90 * mm, 100 * mm])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), TOTAL_BG),
            ("ROUNDEDCORNERS", [8]),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("BOX", (0, 0), (-1, -1), 1, ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(total_table)

        # ── Notes ──
        if quote.notes:
            elements.append(Spacer(1, 8 * mm))
            elements.append(Paragraph("Observações", section_style))
            elements.append(Paragraph(quote.notes, body_style))

        # ── Footer ──
        elements.append(Spacer(1, 10 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=3 * mm))
        elements.append(Paragraph(
            f"{tenant.name} — Proposta gerada automaticamente em {now.strftime('%d/%m/%Y %H:%M')}",
            footer_style,
        ))

        doc.build(elements)
        return buf.getvalue()

    @staticmethod
    def _fmt_currency(value: Optional[float]) -> str:
        if value is None:
            return "—"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
