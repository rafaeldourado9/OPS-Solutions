"""
IngestDocumentsUseCase — RAG ingestion pipeline for company documents.

Supported formats:
  - PDF     → text extracted via PyMuPDF
  - DOCX    → text extracted via python-docx
  - TXT/MD  → read directly
  - Images  → described via LLaVA (Ollama vision model)

Pipeline per file:
  1. Extract raw text (or generate description for images)
  2. Chunk the text with overlap
  3. Embed each chunk via Ollama nomic-embed-text
  4. Upsert each chunk into the Qdrant rules collection

The QdrantAdapter.upsert_document_chunk() handles embedding + upsert.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
from pathlib import Path
from typing import Optional
from uuid import uuid4

from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
from infrastructure.config_loader import BusinessConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported file extensions
# ---------------------------------------------------------------------------

_PDF_EXTS = {".pdf"}
_DOCX_EXTS = {".docx", ".doc"}
_TEXT_EXTS = {".txt", ".md", ".rst"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

SUPPORTED_EXTENSIONS = _PDF_EXTS | _DOCX_EXTS | _TEXT_EXTS | _IMAGE_EXTS

# ---------------------------------------------------------------------------
# Chunking settings
# ---------------------------------------------------------------------------

_DEFAULT_CHUNK_SIZE = 500    # target characters per chunk
_DEFAULT_CHUNK_OVERLAP = 60  # characters of overlap between consecutive chunks


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


def _extract_pdf(path: Path) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    import fitz  # pymupdf

    doc = fitz.open(str(path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(p.strip() for p in pages if p.strip())


def _extract_docx(path: Path) -> str:
    """Extract paragraph text from a DOCX file."""
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_text(path: Path) -> str:
    """Read a plain text file."""
    return path.read_text(encoding="utf-8", errors="replace")


async def _describe_image(path: Path, config: BusinessConfig) -> str:
    """
    Use Gemini Vision to generate a textual description of an image for RAG.
    Returns the description string.
    """
    import google.generativeai as genai

    # Read key from shared file written by CRM Settings (never from env)
    from pathlib import Path as _Path
    _key_file = _Path(os.environ.get("SHARED_GEMINI_KEY_FILE", "/app/shared-agents/.gemini_key"))
    api_key = ""
    try:
        if _key_file.exists():
            api_key = _key_file.read_text().strip()
    except Exception:
        pass
    if not api_key:
        logger.warning("Gemini key not configured — skipping image description for RAG")
        return f"[Imagem: {path.name}]"

    genai.configure(api_key=api_key)
    model_name = config.media.image_model

    image_bytes = path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode()

    # Detect MIME type from magic bytes
    mime = "image/jpeg"
    if image_bytes[:4] == b"\x89PNG":
        mime = "image/png"
    elif image_bytes[:4] == b"RIFF":
        mime = "image/webp"

    prompt = (
        "Descreva esta imagem em detalhes, focando em informações relevantes para "
        "um atendimento comercial: produtos, serviços, preços, procedimentos, "
        "ou qualquer texto visível na imagem. Responda em português brasileiro."
    )

    try:
        loop = asyncio.get_event_loop()

        def _sync_describe():
            model = genai.GenerativeModel(model_name)
            image_part = {"mime_type": mime, "data": b64}
            response = model.generate_content([prompt, image_part])
            return (response.text or "").strip()

        return await loop.run_in_executor(None, _sync_describe)
    except Exception:
        logger.exception("Gemini description failed for image: %s", path.name)
        return f"[Imagem: {path.name}]"


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def chunk_text(
    text: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Strategy:
      1. Split by paragraph (double newline).
      2. If a paragraph fits in the remaining space, add it to the current chunk.
      3. When the chunk is full, save it, then start the next chunk with the
         last `overlap` characters of the previous chunk for continuity.

    Args:
        text:       The input text to chunk.
        chunk_size: Target maximum characters per chunk.
        overlap:    Characters of overlap between consecutive chunks.

    Returns:
        List of non-empty text chunks.
    """
    if not text.strip():
        return []

    # Normalise whitespace between paragraphs
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        if current_len + para_len + 1 <= chunk_size or not current_parts:
            # Fits in the current chunk
            current_parts.append(para)
            current_len += para_len + 1
        else:
            # Save current chunk
            chunk_text_ = "\n\n".join(current_parts)
            chunks.append(chunk_text_)

            # Start next chunk with overlap
            tail = chunk_text_[-overlap:] if overlap else ""
            current_parts = ([tail] if tail else []) + [para]
            current_len = len(tail) + para_len + 1

    # Save the last chunk
    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return [c for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# IngestDocumentsUseCase
# ---------------------------------------------------------------------------


class IngestDocumentsUseCase:
    """
    Ingests company documents into the Qdrant RAG collection.

    Args:
        qdrant: QdrantAdapter with the rules collection pre-configured.
        config: BusinessConfig for the active agent (used for media model).
    """

    def __init__(self, qdrant: QdrantAdapter, config: BusinessConfig) -> None:
        self._qdrant = qdrant
        self._config = config

    async def ingest_file(
        self,
        file_path: Path,
        agent_id: str,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        overlap: int = _DEFAULT_CHUNK_OVERLAP,
    ) -> int:
        """
        Ingest a single file into the RAG collection.

        Args:
            file_path:  Path to the file.
            agent_id:   Agent whose rules collection receives the chunks.
            chunk_size: Target chunk size in characters.
            overlap:    Overlap in characters between consecutive chunks.

        Returns:
            Number of chunks stored.
        """
        ext = file_path.suffix.lower()
        source = file_path.name

        logger.info("Ingesting %s (type=%s) for agent=%s", source, ext, agent_id)

        # 1. Extract text
        if ext in _PDF_EXTS:
            text = _extract_pdf(file_path)
        elif ext in _DOCX_EXTS:
            text = _extract_docx(file_path)
        elif ext in _TEXT_EXTS:
            text = _extract_text(file_path)
        elif ext in _IMAGE_EXTS:
            text = await _describe_image(file_path, self._config)
        else:
            logger.warning("Unsupported file type: %s — skipping", source)
            return 0

        if not text.strip():
            logger.warning("No text extracted from %s — skipping", source)
            return 0

        # 2. Chunk
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        logger.info("  → %d chunks from %s", len(chunks), source)

        # 3. Embed + upsert each chunk
        stored = 0
        for i, chunk in enumerate(chunks):
            point_id = str(uuid4())
            try:
                await self._qdrant.upsert_document_chunk(
                    point_id=point_id,
                    text=chunk,
                    agent_id=agent_id,
                    source=source,
                    chunk_index=i,
                )
                stored += 1
            except Exception:
                logger.exception(
                    "Failed to store chunk %d from %s — continuing", i, source
                )

        logger.info("  → stored %d/%d chunks from %s", stored, len(chunks), source)
        return stored

    async def ingest_directory(
        self,
        dir_path: Path,
        agent_id: str,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        overlap: int = _DEFAULT_CHUNK_OVERLAP,
    ) -> int:
        """
        Recursively ingest all supported files in a directory.

        Args:
            dir_path:  Directory to scan.
            agent_id:  Target agent.
            chunk_size, overlap: Passed to ingest_file.

        Returns:
            Total number of chunks stored across all files.
        """
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        files = [
            f for f in dir_path.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not files:
            logger.warning("No supported files found in %s", dir_path)
            return 0

        logger.info(
            "Ingesting %d file(s) from %s for agent=%s", len(files), dir_path, agent_id
        )

        total = 0
        for file_path in sorted(files):
            try:
                total += await self.ingest_file(
                    file_path, agent_id, chunk_size=chunk_size, overlap=overlap
                )
            except Exception:
                logger.exception("Ingest failed for %s — skipping", file_path.name)

        logger.info("Ingest complete: %d total chunks for agent=%s", total, agent_id)
        return total
