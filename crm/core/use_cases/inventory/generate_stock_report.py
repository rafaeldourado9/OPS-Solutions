from __future__ import annotations

import io
from collections import defaultdict
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

from core.domain.product import MovementType, Product, StockMovement
from core.domain.tenant import Tenant
from core.ports.outbound.product_repository import ProductRepositoryPort
from core.ports.outbound.stock_movement_repository import StockMovementRepositoryPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


ACCENT = colors.HexColor("#0ABAB5")
HEADER_BG = colors.HexColor("#F4F4F5")
BORDER_COLOR = colors.HexColor("#E4E4E7")


class GenerateStockReportUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        product_repo: ProductRepositoryPort,
        movement_repo: StockMovementRepositoryPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._product_repo = product_repo
        self._movement_repo = movement_repo

    async def execute(self, tenant_id: UUID) -> bytes:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        products, _ = await self._product_repo.list_by_tenant(
            tenant_id, active_only=True, offset=0, limit=1000
        )

        product_ids = [p.id for p in products]
        movements, _ = await self._movement_repo.list_by_tenant(
            tenant_id, product_ids=product_ids, offset=0, limit=2000
        )

        # Group movements by product
        movements_by_product: dict[UUID, list[StockMovement]] = defaultdict(list)
        for m in movements:
            movements_by_product[m.product_id].append(m)

        return self._build_pdf(tenant, products, movements_by_product)

    def _build_pdf(
        self,
        tenant: Tenant,
        products: list[Product],
        movements_by_product: dict[UUID, list[StockMovement]],
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
        normal_style = ParagraphStyle(
            "ReportNormal",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#3F3F46"),
        )

        elements = []
        now = datetime.now()

        # ── Header ──
        elements.append(Paragraph(tenant.name, title_style))
        elements.append(Paragraph(
            f"Relatório de Estoque — Gerado em {now.strftime('%d/%m/%Y às %H:%M')}",
            subtitle_style,
        ))
        elements.append(Spacer(1, 4 * mm))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=ACCENT, spaceAfter=6 * mm
        ))

        # ── Summary ──
        total_products = len(products)
        total_stock = sum(p.stock_quantity for p in products)
        total_value = sum(p.stock_quantity * (p.price or 0) for p in products)
        low_stock = sum(1 for p in products if p.is_low_stock)
        total_entries = sum(
            1 for ms in movements_by_product.values() for m in ms if m.type == MovementType.IN
        )
        total_exits = sum(
            1 for ms in movements_by_product.values() for m in ms if m.type == MovementType.OUT
        )

        summary_data = [
            ["Total de Produtos", str(total_products)],
            ["Itens em Estoque", f"{total_stock:,.0f}"],
            ["Valor Total em Estoque", self._fmt_currency(total_value)],
            ["Produtos com Estoque Baixo", str(low_stock)],
            ["Total de Entradas", str(total_entries)],
            ["Total de Saídas", str(total_exits)],
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

        # ── Products Table ──
        elements.append(Paragraph("Produtos em Estoque", section_style))

        product_header = ["Produto", "SKU", "Categoria", "Preço", "Estoque", "Mínimo", "Status"]
        product_rows = [product_header]
        for p in sorted(products, key=lambda x: x.name):
            status = "Crítico" if p.stock_quantity <= 0 else ("Baixo" if p.is_low_stock else "Normal")
            product_rows.append([
                p.name,
                p.sku,
                p.description or "-",
                self._fmt_currency(p.price) if p.price is not None else "-",
                str(int(p.stock_quantity)),
                str(int(p.min_stock_alert)),
                status,
            ])

        col_widths = [50 * mm, 25 * mm, 30 * mm, 22 * mm, 18 * mm, 18 * mm, 17 * mm]
        product_table = Table(product_rows, colWidths=col_widths, repeatRows=1)
        product_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#71717A")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#3F3F46")),
            ("ALIGN", (3, 0), (5, -1), "RIGHT"),
            ("ALIGN", (6, 0), (6, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER_COLOR),
            ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#F4F4F5")),
            ("LINEBELOW", (0, -1), (-1, -1), 1, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(product_table)
        elements.append(Spacer(1, 8 * mm))

        # ── Movements Table ──
        elements.append(Paragraph("Histórico de Movimentações", section_style))

        if not any(movements_by_product.values()):
            elements.append(Paragraph("Nenhuma movimentação registrada.", normal_style))
        else:
            product_map = {p.id: p for p in products}
            mov_header = ["Data", "Produto", "Tipo", "Qtd", "Motivo"]
            mov_rows = [mov_header]

            all_movements = []
            for ms in movements_by_product.values():
                all_movements.extend(ms)
            all_movements.sort(key=lambda m: m.created_at, reverse=True)

            for m in all_movements[:200]:
                pname = product_map.get(m.product_id)
                type_label = (
                    "Entrada" if m.type == MovementType.IN else
                    "Saída" if m.type == MovementType.OUT else
                    "Ajuste"
                )
                sign = "+" if m.type == MovementType.IN else ("-" if m.type == MovementType.OUT else "=")
                mov_rows.append([
                    m.created_at.strftime("%d/%m/%Y %H:%M"),
                    pname.name if pname else str(m.product_id)[:8],
                    type_label,
                    f"{sign}{int(m.quantity)}",
                    m.reason or "-",
                ])

            mov_col_widths = [30 * mm, 45 * mm, 20 * mm, 18 * mm, 67 * mm]
            mov_table = Table(mov_rows, colWidths=mov_col_widths, repeatRows=1)
            mov_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#71717A")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#3F3F46")),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER_COLOR),
                ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#F4F4F5")),
                ("LINEBELOW", (0, -1), (-1, -1), 1, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(mov_table)

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
    def _fmt_currency(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
