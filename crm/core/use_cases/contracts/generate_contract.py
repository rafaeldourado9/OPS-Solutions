from uuid import UUID

from core.ports.outbound.contract_template_repository import ContractTemplateRepositoryPort
from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort
from core.ports.outbound.storage_port import StoragePort


class PdfExporterPort:
    """Minimal interface for PDF conversion — matches LibreOfficePdfExporter."""

    def convert(self, docx_bytes: bytes) -> bytes:
        raise NotImplementedError


class GenerateContractUseCase:

    def __init__(
        self,
        template_repo: ContractTemplateRepositoryPort,
        storage: StoragePort,
        docx_engine: DocxTemplateEnginePort,
        pdf_exporter: PdfExporterPort,
    ) -> None:
        self._repo = template_repo
        self._storage = storage
        self._docx_engine = docx_engine
        self._pdf_exporter = pdf_exporter

    async def execute(
        self,
        tenant_id: UUID,
        template_id: UUID,
        variable_values: dict[str, str],
    ) -> bytes:
        template = await self._repo.get_by_id(tenant_id, template_id)
        if not template:
            raise ValueError("Contract template not found")

        docx_bytes = await self._storage.download(template.file_key)
        filled_docx = self._docx_engine.fill_template(docx_bytes, variable_values)
        return self._pdf_exporter.convert(filled_docx)
