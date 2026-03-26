from abc import ABC, abstractmethod


class DocxTemplateEnginePort(ABC):

    @abstractmethod
    def extract_placeholders(self, docx_bytes: bytes) -> list[str]:
        """Returns all unique placeholder names found in the DOCX (e.g. 'nome_cliente')."""
        ...

    @abstractmethod
    def fill_template(self, docx_bytes: bytes, context: dict[str, str]) -> bytes:
        """Replaces {key} patterns in the DOCX with values from context. Returns filled DOCX bytes."""
        ...
