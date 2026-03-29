from dataclasses import dataclass
from uuid import UUID

from core.domain.quote_template import KNOWN_CRM_FIELDS
from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort
from core.ports.outbound.llm_analyzer_port import FieldSuggestion, LLMAnalyzerPort


@dataclass(frozen=True)
class AnalyzeTemplateFieldsRequest:
    tenant_id: UUID
    docx_bytes: bytes


@dataclass(frozen=True)
class AnalyzeTemplateFieldsResult:
    suggestions: list[FieldSuggestion]
    document_text_preview: str  # First 500 chars, for UI display


class AnalyzeTemplateFieldsUseCase:
    """
    Analyze a DOCX template with AI to suggest placeholder mappings.

    Works on "virgin" documents (no {placeholders} yet). The LLM inspects
    the raw text and proposes which spans should become dynamic fields.
    """

    def __init__(
        self,
        docx_engine: DocxTemplateEnginePort,
        llm_analyzer: LLMAnalyzerPort,
    ) -> None:
        self._engine = docx_engine
        self._llm = llm_analyzer

    async def execute(
        self, request: AnalyzeTemplateFieldsRequest
    ) -> AnalyzeTemplateFieldsResult:
        document_text = self._engine.extract_text(request.docx_bytes)

        suggestions = await self._llm.analyze_document_fields(
            document_text=document_text,
            known_crm_fields=KNOWN_CRM_FIELDS,
        )

        return AnalyzeTemplateFieldsResult(
            suggestions=suggestions,
            document_text_preview=document_text[:500],
        )
