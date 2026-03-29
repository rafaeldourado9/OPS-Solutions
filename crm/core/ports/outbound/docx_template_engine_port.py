from abc import ABC, abstractmethod


class DocxTemplateEnginePort(ABC):

    @abstractmethod
    def extract_placeholders(self, docx_bytes: bytes) -> list[str]:
        """Returns all unique placeholder names found in the DOCX (e.g. 'nome_cliente')."""
        ...

    @abstractmethod
    def extract_text(self, docx_bytes: bytes) -> str:
        """Returns all plain text from the DOCX (paragraphs joined by newlines)."""
        ...

    @abstractmethod
    def fill_template(self, docx_bytes: bytes, context: dict[str, str]) -> bytes:
        """Replaces {key} patterns in the DOCX with values from context. Returns filled DOCX bytes."""
        ...

    @abstractmethod
    def inject_placeholders(
        self, docx_bytes: bytes, injections: dict[str, str]
    ) -> bytes:
        """
        Replace literal text spans with {placeholder} syntax.

        Args:
            docx_bytes: Original DOCX without placeholders.
            injections: Maps original_text → placeholder_key.
                        e.g. {"R$ 0,00": "valor_total", "NOME DO CLIENTE": "nome_cliente"}

        Returns:
            Modified DOCX bytes where each original_text has been replaced by {placeholder_key}.
        """
        ...
