"""Port for document generation (PDF reports)."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class DocumentPort(ABC):
    """Interface for document generation adapters."""

    @abstractmethod
    async def generate_pdf(
        self,
        template_data: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Generate a PDF document from template data.

        Args:
            template_data: Dictionary with template variables
            output_path: Path to save the generated PDF

        Returns:
            Path to the generated PDF file
        """
        pass
