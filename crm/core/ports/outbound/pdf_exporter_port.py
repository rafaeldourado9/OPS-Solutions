from abc import ABC, abstractmethod


class PdfExporterPort(ABC):

    @abstractmethod
    async def convert(self, docx_bytes: bytes) -> bytes:
        """Converts DOCX bytes to PDF bytes."""
        ...
