"""
Unit tests for IngestDocumentsUseCase and the chunk_text() helper.

No Qdrant or Ollama required — the QdrantAdapter is fully mocked.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.use_cases.ingest_documents import IngestDocumentsUseCase, chunk_text
from infrastructure.config_loader import (
    AgentConfig,
    AntiHallucinationConfig,
    BusinessConfig,
    CRMConfig,
    LLMConfig,
    MediaConfig,
    MemoryConfig,
    MessagingConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> BusinessConfig:
    return BusinessConfig(
        agent=AgentConfig(name="Test", company="Test Co"),
        llm=LLMConfig(provider="ollama", model="llama3.1:8b"),
        messaging=MessagingConfig(),
        memory=MemoryConfig(
            qdrant_collection="test_chats",
            qdrant_rag_collection="test_rules",
        ),
        anti_hallucination=AntiHallucinationConfig(),
        media=MediaConfig(image_model="llava:13b"),
        crm=CRMConfig(enabled=False),
    )


def _make_qdrant_mock() -> MagicMock:
    qdrant = MagicMock()
    qdrant.upsert_document_chunk = AsyncMock()
    return qdrant


# ---------------------------------------------------------------------------
# chunk_text() tests
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []

    def test_short_text_is_single_chunk(self):
        text = "Este é um texto curto."
        chunks = chunk_text(text, chunk_size=500)
        assert chunks == [text]

    def test_text_longer_than_chunk_size_is_split(self):
        para = "A" * 300
        text = f"{para}\n\n{para}"
        chunks = chunk_text(text, chunk_size=350, overlap=0)
        assert len(chunks) == 2

    def test_overlap_carries_tail_to_next_chunk(self):
        para1 = "Parágrafo 1. " * 20   # ~260 chars
        para2 = "Parágrafo 2. " * 20
        text = f"{para1.strip()}\n\n{para2.strip()}"
        chunks = chunk_text(text, chunk_size=300, overlap=50)
        assert len(chunks) >= 2
        # The second chunk should start with the tail of the first
        assert chunks[1][:50] in chunks[0] or len(chunks[0]) < 50

    def test_no_empty_chunks(self):
        text = "Para 1\n\n\n\nPara 2\n\n"
        chunks = chunk_text(text)
        assert all(c.strip() for c in chunks)

    def test_whitespace_only_returns_empty(self):
        assert chunk_text("   \n\n   ") == []

    def test_single_large_paragraph_kept_whole(self):
        big_para = "Palavra " * 100  # ~800 chars
        chunks = chunk_text(big_para, chunk_size=500)
        # Large single paragraph: first chunk is the whole thing (no split point)
        assert len(chunks) >= 1
        assert big_para.strip() in "".join(chunks)

    def test_multiple_small_paragraphs_grouped(self):
        # 10 paragraphs of 30 chars each → should fit several per chunk
        paras = "\n\n".join(["Parágrafo curto aqui."] * 10)
        chunks = chunk_text(paras, chunk_size=500)
        # Should be fewer chunks than paragraphs
        assert len(chunks) < 10


# ---------------------------------------------------------------------------
# IngestDocumentsUseCase tests
# ---------------------------------------------------------------------------


class TestIngestDocumentsUseCase:
    @pytest.mark.asyncio
    async def test_ingest_txt_file(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("Linha 1\n\nLinha 2\n\nLinha 3")
            tmp_path = Path(f.name)

        try:
            count = await uc.ingest_file(tmp_path, agent_id="test_agent")
            assert count >= 1
            assert qdrant.upsert_document_chunk.await_count == count
        finally:
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_ingest_empty_file_returns_zero(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("   ")
            tmp_path = Path(f.name)

        try:
            count = await uc.ingest_file(tmp_path, agent_id="test_agent")
            assert count == 0
            qdrant.upsert_document_chunk.assert_not_awaited()
        finally:
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_ingest_unsupported_extension_returns_zero(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode="w") as f:
            f.write("conteudo")
            tmp_path = Path(f.name)

        try:
            count = await uc.ingest_file(tmp_path, agent_id="test_agent")
            assert count == 0
        finally:
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_upsert_failure_does_not_abort_remaining_chunks(self):
        qdrant = _make_qdrant_mock()
        # First call fails, second succeeds
        qdrant.upsert_document_chunk = AsyncMock(
            side_effect=[Exception("Qdrant down"), None, None]
        )
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        # Create a text with multiple chunks
        big_text = "\n\n".join(["Parágrafo " * 30] * 5)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write(big_text)
            tmp_path = Path(f.name)

        try:
            count = await uc.ingest_file(tmp_path, agent_id="test_agent")
            # Should have stored some chunks despite one failure
            assert count >= 1
        finally:
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_ingest_directory_processes_multiple_files(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            for i in range(3):
                (dir_path / f"doc_{i}.txt").write_text(
                    f"Documento {i} com conteúdo relevante para testes.\n\nSegundo parágrafo."
                )

            total = await uc.ingest_directory(dir_path, agent_id="test_agent")
            assert total >= 3

    @pytest.mark.asyncio
    async def test_ingest_directory_not_found_raises(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        with pytest.raises(FileNotFoundError):
            await uc.ingest_directory(Path("/nonexistent/path"), agent_id="test_agent")

    @pytest.mark.asyncio
    async def test_ingest_directory_empty_returns_zero(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        with tempfile.TemporaryDirectory() as tmpdir:
            total = await uc.ingest_directory(Path(tmpdir), agent_id="test_agent")
            assert total == 0

    @pytest.mark.asyncio
    async def test_chunk_size_controls_number_of_chunks(self):
        qdrant = _make_qdrant_mock()
        config = _make_config()
        uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

        # Large text that will definitely need multiple chunks at size=100
        text = "\n\n".join(["Parágrafo de texto aqui com mais de cem caracteres."] * 10)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write(text)
            tmp_path = Path(f.name)

        try:
            count_small = await uc.ingest_file(
                tmp_path, agent_id="test_agent", chunk_size=100, overlap=0
            )
            qdrant.upsert_document_chunk.reset_mock()

            count_large = await uc.ingest_file(
                tmp_path, agent_id="test_agent", chunk_size=1000, overlap=0
            )
            # Smaller chunk size → more chunks
            assert count_small > count_large
        finally:
            tmp_path.unlink()
