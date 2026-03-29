from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FieldSuggestion:
    """A single AI-suggested field mapping from original DOCX text to a CRM placeholder."""
    original_text: str    # Exact text found in the document (e.g. "R$ 0,00")
    placeholder_key: str  # snake_case key to use (e.g. "valor_total")
    crm_field: str        # Matching CRM field key or "__manual__"
    description: str      # Human-readable explanation
    confidence: float = field(default=1.0)


class LLMAnalyzerPort(ABC):

    @abstractmethod
    async def analyze_document_fields(
        self,
        document_text: str,
        known_crm_fields: dict[str, str],
    ) -> list[FieldSuggestion]:
        """
        Analyze document text and return suggested placeholder mappings.

        Args:
            document_text:    Full text extracted from the DOCX.
            known_crm_fields: Dict of {crm_key: label} from KNOWN_CRM_FIELDS.

        Returns:
            List of FieldSuggestion ordered by confidence descending.
        """
        ...
