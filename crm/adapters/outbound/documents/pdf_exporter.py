import asyncio
import os
import tempfile

from core.ports.outbound.pdf_exporter_port import PdfExporterPort


class LibreOfficePdfExporter(PdfExporterPort):
    """Converts DOCX to PDF using LibreOffice headless."""

    async def convert(self, docx_bytes: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, "input.docx")
            pdf_path = os.path.join(tmpdir, "input.pdf")

            with open(docx_path, "wb") as f:
                f.write(docx_bytes)

            proc = await asyncio.create_subprocess_exec(
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", tmpdir,
                docx_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice conversion failed (rc={proc.returncode}): {stderr.decode()}"
                )

            if not os.path.exists(pdf_path):
                raise RuntimeError("LibreOffice did not produce output PDF")

            with open(pdf_path, "rb") as f:
                return f.read()
