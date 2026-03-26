import io
import re

from docx import Document

from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class DocxTemplateEngine(DocxTemplateEnginePort):

    def extract_placeholders(self, docx_bytes: bytes) -> list[str]:
        doc = Document(io.BytesIO(docx_bytes))
        found: set[str] = set()

        for para in doc.paragraphs:
            for match in PLACEHOLDER_RE.finditer(para.text):
                found.add(match.group(1))

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for match in PLACEHOLDER_RE.finditer(para.text):
                            found.add(match.group(1))

        return sorted(found)

    def fill_template(self, docx_bytes: bytes, context: dict[str, str]) -> bytes:
        doc = Document(io.BytesIO(docx_bytes))

        for para in doc.paragraphs:
            self._replace_in_paragraph(para, context)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, context)

        output = io.BytesIO()
        doc.save(output)
        return output.getvalue()

    @staticmethod
    def _replace_in_paragraph(para, context: dict[str, str]) -> None:
        full_text = para.text
        if "{" not in full_text:
            return

        def replacer(m: re.Match) -> str:
            key = m.group(1)
            return context.get(key, m.group(0))

        replaced = PLACEHOLDER_RE.sub(replacer, full_text)
        if replaced == full_text:
            return

        # Clear all runs and put result in first run, preserving its formatting
        if para.runs:
            para.runs[0].text = replaced
            for run in para.runs[1:]:
                run.text = ""
        else:
            para.add_run(replaced)
