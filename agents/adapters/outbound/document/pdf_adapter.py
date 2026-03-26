"""PDF Document Generator using ReportLab."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from core.ports.document_port import DocumentPort

logger = logging.getLogger(__name__)


class PDFDocumentAdapter(DocumentPort):
    """Generate PDF reports using ReportLab."""

    def __init__(self, template_path: str):
        """
        Initialize PDF generator.

        Args:
            template_path: Path to template file (for reference)
        """
        self.template_path = template_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold',
        ))

        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold',
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        ))

    async def generate_pdf(
        self,
        template_data: Dict[str, Any],
        output_path: str,
    ) -> str:
        """Generate PDF from template data."""
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            # Build content
            story = []
            story.extend(self._build_header(template_data))
            story.extend(self._build_client_info(template_data))
            story.extend(self._build_business_context(template_data))
            story.extend(self._build_current_situation(template_data))
            story.extend(self._build_requirements(template_data))
            story.extend(self._build_non_functional(template_data))
            story.extend(self._build_constraints(template_data))
            story.extend(self._build_solution(template_data))
            story.extend(self._build_estimates(template_data))
            story.extend(self._build_next_steps(template_data))
            story.extend(self._build_attachments(template_data))

            # Generate PDF
            doc.build(story)

            logger.info(f"PDF generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.exception(f"Failed to generate PDF: {e}")
            raise

    def _build_header(self, data: Dict[str, Any]) -> list:
        """Build document header."""
        story = []
        
        # Title
        story.append(Paragraph(
            "Levantamento de Requisitos",
            self.styles['CustomTitle']
        ))
        
        # Company logo/name
        story.append(Paragraph(
            "<b>OPS Solution</b> - Consultoria em Arquitetura de Software",
            self.styles['BodyText']
        ))
        
        story.append(Spacer(1, 0.5*cm))
        
        # Horizontal line
        story.append(Table(
            [['']], 
            colWidths=[17*cm],
            style=TableStyle([
                ('LINEABOVE', (0,0), (-1,0), 2, colors.HexColor('#2c3e50')),
            ])
        ))
        
        story.append(Spacer(1, 0.5*cm))
        
        return story

    def _build_client_info(self, data: Dict[str, Any]) -> list:
        """Build client information section."""
        story = []
        
        story.append(Paragraph("INFORMAÇÕES DO CLIENTE", self.styles['SectionHeader']))
        
        info_data = [
            ['Cliente:', data.get('NOME_CLIENTE', 'N/A')],
            ['Contato:', data.get('TELEFONE', 'N/A')],
            ['Data:', data.get('DATA', datetime.now().strftime('%d/%m/%Y'))],
            ['Consultor:', 'Rafael - OPS Solution'],
        ]
        
        table = Table(info_data, colWidths=[4*cm, 13*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
        
        return story

    def _build_business_context(self, data: Dict[str, Any]) -> list:
        """Build business context section."""
        story = []
        
        story.append(Paragraph("1. CONTEXTO DO NEGÓCIO", self.styles['SectionHeader']))
        
        story.append(Paragraph("1.1 Descrição do Problema", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('DESCRICAO_PROBLEMA', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("1.2 Dor Principal", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('DOR_PRINCIPAL', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("1.3 Impacto no Negócio", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('IMPACTO_NEGOCIO', 'Não informado'), self.styles['BodyText']))
        
        return story

    def _build_current_situation(self, data: Dict[str, Any]) -> list:
        """Build current situation section."""
        story = []
        
        story.append(Paragraph("2. SITUAÇÃO ATUAL", self.styles['SectionHeader']))
        
        story.append(Paragraph("2.1 Como Funciona Hoje", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('SITUACAO_ATUAL', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("2.2 Sistemas Existentes", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('SISTEMAS_EXISTENTES', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("2.3 Principais Problemas", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('PROBLEMAS_ATUAIS', 'Não informado'), self.styles['BodyText']))
        
        return story

    def _build_requirements(self, data: Dict[str, Any]) -> list:
        """Build functional requirements section."""
        story = []
        
        story.append(Paragraph("3. REQUISITOS FUNCIONAIS", self.styles['SectionHeader']))
        
        story.append(Paragraph("3.1 Funcionalidades Principais", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('FUNCIONALIDADES', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("3.2 Usuários do Sistema", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('USUARIOS', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("3.3 Fluxos Principais", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('FLUXOS', 'Não informado'), self.styles['BodyText']))
        
        return story

    def _build_non_functional(self, data: Dict[str, Any]) -> list:
        """Build non-functional requirements section."""
        story = []
        
        story.append(Paragraph("4. REQUISITOS NÃO-FUNCIONAIS", self.styles['SectionHeader']))
        
        story.append(Paragraph("4.1 Escala e Volume", self.styles['SubsectionHeader']))
        
        scale_data = [
            ['Usuários simultâneos:', data.get('USUARIOS_SIMULTANEOS', 'N/A')],
            ['Transações/dia:', data.get('TRANSACOES_DIA', 'N/A')],
            ['Volume de dados:', data.get('VOLUME_DADOS', 'N/A')],
            ['Crescimento esperado:', data.get('CRESCIMENTO', 'N/A')],
        ]
        
        table = Table(scale_data, colWidths=[5*cm, 12*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*cm))
        
        story.append(Paragraph("4.2 Performance", self.styles['SubsectionHeader']))
        story.append(Paragraph(f"Latência: {data.get('LATENCIA', 'N/A')}", self.styles['BodyText']))
        story.append(Paragraph(f"Disponibilidade: {data.get('DISPONIBILIDADE', 'N/A')}", self.styles['BodyText']))
        
        story.append(Paragraph("4.3 Segurança", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('REQUISITOS_SEGURANCA', 'Não informado'), self.styles['BodyText']))
        
        return story

    def _build_constraints(self, data: Dict[str, Any]) -> list:
        """Build constraints section."""
        story = []
        
        story.append(Paragraph("5. RESTRIÇÕES", self.styles['SectionHeader']))
        
        story.append(Paragraph("5.1 Prazo", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('PRAZO', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("5.2 Orçamento", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('ORCAMENTO', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("5.3 Tecnologias Obrigatórias", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('TECNOLOGIAS_OBRIGATORIAS', 'Não informado'), self.styles['BodyText']))
        
        story.append(Paragraph("5.4 Compliance", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('COMPLIANCE', 'Não informado'), self.styles['BodyText']))
        
        return story

    def _build_solution(self, data: Dict[str, Any]) -> list:
        """Build proposed solution section."""
        story = []
        
        story.append(Paragraph("6. SOLUÇÃO PROPOSTA", self.styles['SectionHeader']))
        
        story.append(Paragraph("6.1 Arquitetura Recomendada", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('ARQUITETURA', 'A definir'), self.styles['BodyText']))
        
        story.append(Paragraph("6.2 Tecnologias Sugeridas", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('TECNOLOGIAS', 'A definir'), self.styles['BodyText']))
        
        story.append(Paragraph("6.3 Fases de Implementação", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('FASES', 'A definir'), self.styles['BodyText']))
        
        return story

    def _build_estimates(self, data: Dict[str, Any]) -> list:
        """Build estimates section."""
        story = []
        
        story.append(Paragraph("7. ESTIMATIVAS", self.styles['SectionHeader']))
        
        story.append(Paragraph("7.1 Tempo de Desenvolvimento", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('TEMPO_DESENVOLVIMENTO', 'A estimar'), self.styles['BodyText']))
        
        story.append(Paragraph("7.2 Custo Estimado", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('CUSTO_ESTIMADO', 'A estimar'), self.styles['BodyText']))
        
        story.append(Paragraph("7.3 Equipe Necessária", self.styles['SubsectionHeader']))
        story.append(Paragraph(data.get('EQUIPE', 'A definir'), self.styles['BodyText']))
        
        return story

    def _build_next_steps(self, data: Dict[str, Any]) -> list:
        """Build next steps section."""
        story = []
        
        story.append(Paragraph("8. PRÓXIMOS PASSOS", self.styles['SectionHeader']))
        story.append(Paragraph(data.get('PROXIMOS_PASSOS', 'A definir'), self.styles['BodyText']))
        
        story.append(Paragraph("9. OBSERVAÇÕES ADICIONAIS", self.styles['SectionHeader']))
        story.append(Paragraph(data.get('OBSERVACOES', 'Nenhuma'), self.styles['BodyText']))
        
        return story

    def _build_attachments(self, data: Dict[str, Any]) -> list:
        """Build attachments section."""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("10. ANEXOS", self.styles['SectionHeader']))
        
        # Audio transcriptions
        if data.get('TRANSCRICOES_AUDIO'):
            story.append(Paragraph("10.1 Transcrições de Áudio", self.styles['SubsectionHeader']))
            story.append(Paragraph(data['TRANSCRICOES_AUDIO'], self.styles['BodyText']))
        
        # Image descriptions
        if data.get('IMAGENS_DESCRICOES'):
            story.append(Paragraph("10.2 Imagens Compartilhadas", self.styles['SubsectionHeader']))
            story.append(Paragraph(data['IMAGENS_DESCRICOES'], self.styles['BodyText']))
        
        # Conversation history
        if data.get('HISTORICO_CONVERSA'):
            story.append(Paragraph("10.3 Histórico da Conversa", self.styles['SubsectionHeader']))
            story.append(Paragraph(data['HISTORICO_CONVERSA'], self.styles['BodyText']))
        
        # Footer
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"<i>Documento gerado automaticamente pelo sistema OPS Solution em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>",
            self.styles['BodyText']
        ))
        
        return story
