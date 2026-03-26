"""
Unit tests for the media pipeline:
  - MultimodalAdapter (with mocked HTTP calls)
  - waha_webhook media processing helpers
  - NullMediaAdapter
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapters.outbound.media.null_media_adapter import NullMediaAdapter
from adapters.outbound.media.multimodal_adapter import MultimodalAdapter, _extract_frames_sync


# ---------------------------------------------------------------------------
# NullMediaAdapter
# ---------------------------------------------------------------------------


class TestNullMediaAdapter:
    @pytest.mark.asyncio
    async def test_transcribe_returns_empty(self):
        adapter = NullMediaAdapter()
        result = await adapter.transcribe_audio(b"fake audio bytes")
        assert result == ""

    @pytest.mark.asyncio
    async def test_describe_image_returns_empty(self):
        adapter = NullMediaAdapter()
        result = await adapter.describe_image(b"fake image bytes")
        assert result == ""

    @pytest.mark.asyncio
    async def test_describe_video_returns_empty(self):
        adapter = NullMediaAdapter()
        result = await adapter.describe_video(b"fake video bytes")
        assert result == ""


# ---------------------------------------------------------------------------
# MultimodalAdapter — audio
# ---------------------------------------------------------------------------


class TestMultimodalAdapterAudio:
    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        adapter = MultimodalAdapter(audio_model="whisper:test", image_model="llava:test")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "olá, preciso de ajuda"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await adapter.transcribe_audio(b"audio bytes")

        assert result == "olá, preciso de ajuda"

    @pytest.mark.asyncio
    async def test_transcribe_failure_returns_empty(self):
        adapter = MultimodalAdapter(audio_model="whisper:test", image_model="llava:test")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client_cls.return_value = mock_client

            result = await adapter.transcribe_audio(b"audio bytes")

        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_empty_response_returns_empty(self):
        adapter = MultimodalAdapter(audio_model="whisper:test", image_model="llava:test")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": ""}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await adapter.transcribe_audio(b"audio bytes")

        assert result == ""


# ---------------------------------------------------------------------------
# MultimodalAdapter — image
# ---------------------------------------------------------------------------


class TestMultimodalAdapterImage:
    @pytest.mark.asyncio
    async def test_describe_image_success(self):
        adapter = MultimodalAdapter(audio_model="whisper:test", image_model="llava:test")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Foto de um produto danificado com arranhões."}
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await adapter.describe_image(b"image bytes")

        assert "produto danificado" in result

    @pytest.mark.asyncio
    async def test_describe_image_failure_returns_empty(self):
        adapter = MultimodalAdapter(audio_model="whisper:test", image_model="llava:test")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=Exception("timeout"))
            mock_client_cls.return_value = mock_client

            result = await adapter.describe_image(b"image bytes")

        assert result == ""


# ---------------------------------------------------------------------------
# waha_webhook media processing helpers
# ---------------------------------------------------------------------------


class TestWebhookMediaProcessing:
    @pytest.mark.asyncio
    async def test_process_audio_builds_transcription_string(self):
        from adapters.inbound.waha_webhook import _process_media

        mock_media = AsyncMock()
        mock_media.transcribe_audio = AsyncMock(return_value="quero saber o prazo")

        with patch("adapters.inbound.waha_webhook._fetch_media_bytes", return_value=b"audio"):
            payload = {"type": "ptt", "hasMedia": True, "mediaUrl": "http://waha/file.ogg", "id": "x"}
            result = await _process_media(payload, mock_media, "http://localhost:3000", "", "default", "5511@c.us")

        assert "quero saber o prazo" in result
        assert "[contexto: mensagem de voz" in result

    @pytest.mark.asyncio
    async def test_process_image_builds_description_string(self):
        from adapters.inbound.waha_webhook import _process_media

        mock_media = AsyncMock()
        mock_media.describe_image = AsyncMock(return_value="produto com defeito visível")

        with patch("adapters.inbound.waha_webhook._fetch_media_bytes", return_value=b"img"):
            payload = {"type": "image", "hasMedia": True, "mediaUrl": "http://waha/file.jpg", "caption": "Veja", "id": "x"}
            result = await _process_media(payload, mock_media, "http://localhost:3000", "", "default", "5511@c.us")

        assert "[Usuário enviou uma imagem" in result
        assert "produto com defeito" in result

    @pytest.mark.asyncio
    async def test_process_media_no_url_returns_fallback(self):
        from adapters.inbound.waha_webhook import _process_media

        mock_media = AsyncMock()
        with patch("adapters.inbound.waha_webhook._fetch_media_bytes", return_value=None):
            payload = {"type": "ptt", "hasMedia": True, "mediaUrl": "", "id": "x"}
            result = await _process_media(payload, mock_media, "http://localhost:3000", "", "default", "5511@c.us")

        assert "áudio" in result

    @pytest.mark.asyncio
    async def test_process_media_download_failure_returns_fallback(self):
        from adapters.inbound.waha_webhook import _process_media

        mock_media = AsyncMock()
        with patch("adapters.inbound.waha_webhook._fetch_media_bytes", return_value=None):
            payload = {"type": "image", "hasMedia": True, "mediaUrl": "http://waha/file.jpg", "id": "x"}
            result = await _process_media(payload, mock_media, "http://localhost:3000", "", "default", "5511@c.us")

        assert "imagem" in result

    @pytest.mark.asyncio
    async def test_process_audio_transcription_failure_uses_fallback(self):
        from adapters.inbound.waha_webhook import _process_media

        mock_media = AsyncMock()
        mock_media.transcribe_audio = AsyncMock(return_value="")

        with patch("adapters.inbound.waha_webhook._fetch_media_bytes", return_value=b"audio"):
            payload = {"type": "ptt", "hasMedia": True, "mediaUrl": "http://waha/f.ogg", "id": "x"}
            result = await _process_media(payload, mock_media, "http://localhost:3000", "", "default", "5511@c.us")

        assert "áudio" in result

    @pytest.mark.asyncio
    async def test_queue_helper_serialises_correctly(self):
        from adapters.inbound.waha_webhook import _queue

        debouncer = MagicMock()
        debouncer.push_message = AsyncMock()

        await _queue(debouncer, "5511@c.us", "Olá!")

        debouncer.push_message.assert_awaited_once()
        call_args = debouncer.push_message.await_args
        chat_id_arg = call_args[0][0]
        json_arg = call_args[0][1]

        assert chat_id_arg == "5511@c.us"
        data = json.loads(json_arg)
        assert data["text"] == "Olá!"
        assert data["chat_id"] == "5511@c.us"


# ---------------------------------------------------------------------------
# _fetch_media_bytes — short ID extraction for NOWEB files endpoint
# ---------------------------------------------------------------------------


class TestFetchMediaBytesShortId:
    """NOWEB stores files with the short message ID (after last underscore)."""

    @pytest.mark.asyncio
    async def test_short_id_used_when_full_id_has_at_sign(self):
        """
        Full ID: false_179203215495244@lid_3A07F2B22590D0134AAA
        Short ID: 3A07F2B22590D0134AAA
        Strategy 5 should try the short ID first.
        """
        from adapters.inbound.waha_webhook import _fetch_media_bytes

        payload = {
            "id": "false_179203215495244@lid_3A07F2B22590D0134AAA",
            "hasMedia": True,
            "mediaUrl": "",
            "media": {},
        }

        downloaded_urls: list[str] = []

        async def fake_download(url: str, headers: dict, timeout: float = 30.0):
            downloaded_urls.append(url)
            # Return bytes only when the short ID is used (no @)
            if "3A07F2B22590D0134AAA" in url and "@" not in url.split("/api/files/")[-1]:
                return b"fake_image_bytes"
            return None

        with patch("adapters.inbound.waha_webhook._download_url", side_effect=fake_download):
            result = await _fetch_media_bytes(
                payload,
                waha_url="http://waha:3000",
                api_key="",
                session="default",
                chat_id="179203215495244@lid",
            )

        assert result == b"fake_image_bytes"
        # The first attempt with the short ID (no extension) must have matched
        short_id_urls = [u for u in downloaded_urls if "3A07F2B22590D0134AAA" in u and "@" not in u.split("/api/files/")[-1]]
        assert len(short_id_urls) > 0, "Short ID URL was never tried"

    @pytest.mark.asyncio
    async def test_fallback_to_full_id_when_short_fails(self):
        """If the short ID also fails, the full ID is tried as fallback."""
        from adapters.inbound.waha_webhook import _fetch_media_bytes

        payload = {
            "id": "false_123@lid_ABCDEF",
            "hasMedia": True,
            "mediaUrl": "",
            "media": {},
        }

        downloaded_urls: list[str] = []

        async def fake_download(url: str, headers: dict, timeout: float = 30.0):
            downloaded_urls.append(url)
            # Only succeed when full ID is used
            if "false_123@lid_ABCDEF" in url:
                return b"bytes_from_full_id"
            return None

        with patch("adapters.inbound.waha_webhook._download_url", side_effect=fake_download):
            result = await _fetch_media_bytes(
                payload,
                waha_url="http://waha:3000",
                api_key="",
                session="default",
                chat_id="123@lid",
            )

        assert result == b"bytes_from_full_id"


# ---------------------------------------------------------------------------
# Frame extraction (sync) — graceful degradation without ffmpeg
# ---------------------------------------------------------------------------


class TestFrameExtraction:
    def test_returns_empty_when_ffmpeg_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            frames = _extract_frames_sync(b"fake video", interval_seconds=5)
        assert frames == []

    def test_returns_empty_on_ffmpeg_nonzero_exit(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"error"
        with patch("subprocess.run", return_value=mock_result):
            frames = _extract_frames_sync(b"fake video", interval_seconds=5)
        assert frames == []
