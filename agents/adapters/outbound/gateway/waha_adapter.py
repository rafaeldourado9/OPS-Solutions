"""
WAHAAdapter — GatewayPort implementation for the custom WhatsApp Gateway.

Compatible with both WAHA and the custom Baileys-based gateway since they
expose the same REST API. Supports all media types: text, images, audio,
video, documents, and voice messages (PTT).
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Optional

import httpx

from core.ports.gateway_port import GatewayPort
from infrastructure.retry import with_retry

logger = logging.getLogger(__name__)

# API paths (shared by WAHA and custom gateway)
_SEND_TEXT_PATH = "/api/sendText"
_SEND_FILE_PATH = "/api/sendFile"
_SEND_VOICE_PATH = "/api/sendVoice"
_SEND_SEEN_PATH = "/api/sendSeen"
_START_TYPING_PATH = "/api/startTyping"
_STOP_TYPING_PATH = "/api/stopTyping"
_START_RECORDING_PATH = "/api/startRecording"
_STOP_RECORDING_PATH = "/api/stopRecording"


class WAHAAdapter(GatewayPort):
    """
    GatewayPort adapter for the WhatsApp Gateway (WAHA-compatible API).

    Works with both the original WAHA and the custom Baileys-based gateway,
    as they expose the same REST endpoints.

    Uses a shared httpx.AsyncClient with connection pooling to support
    high concurrency without exhausting TCP connections.

    Args:
        base_url: Gateway server base URL (e.g. "http://localhost:3000").
        api_key:  API key (X-Api-Key header). Falls back to WAHA_API_KEY env var.
        session:  Session name (default "default").
        timeout:  HTTP timeout in seconds.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        session: str = "default",
        timeout: float = 15.0,
    ) -> None:
        self._base_url = (
            base_url or os.environ.get("WAHA_URL", "http://localhost:3000")
        ).rstrip("/")
        self._api_key = api_key or os.environ.get("WAHA_API_KEY", "")
        self._session = session
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self, timeout: Optional[float] = None) -> httpx.AsyncClient:
        """Return the shared AsyncClient, creating it lazily on first use."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30,
                ),
                headers=self._headers(),
            )
        return self._client

    async def close(self) -> None:
        """Close the shared HTTP client. Call on shutdown."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["X-Api-Key"] = self._api_key
        return h

    def _chat_id_to_jid(self, chat_id: str) -> str:
        """Ensure chat_id has the required @c.us or @g.us suffix."""
        if "@" in chat_id:
            return chat_id
        return f"{chat_id}@c.us"

    @with_retry(max_retries=3, base_delay=0.5, max_delay=10.0)
    async def send_message(self, chat_id: str, text: str) -> None:
        """Send a plain text message (retries up to 3 times on failure)."""
        url = f"{self._base_url}{_SEND_TEXT_PATH}"
        payload = {
            "chatId": self._chat_id_to_jid(chat_id),
            "text": text,
            "session": self._session,
        }
        try:
            client = self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception:
            logger.exception("send_message failed for chat_id=%s", chat_id)
            raise

    async def send_image(
        self,
        chat_id: str,
        image_data: bytes,
        filename: str = "image.jpg",
        caption: str = "",
    ) -> None:
        """Send an image file via /api/sendFile."""
        mime_type = "image/jpeg" if filename.endswith(".jpg") else "image/png"
        await self._send_file(chat_id, image_data, mime_type, filename, caption)

    async def send_audio(
        self,
        chat_id: str,
        audio_data: bytes,
        filename: str = "audio.mp3",
    ) -> None:
        """Send an audio file via /api/sendFile."""
        mime = "audio/mpeg" if filename.endswith(".mp3") else "audio/ogg; codecs=opus"
        await self._send_file(chat_id, audio_data, mime, filename, timeout=30.0)

    async def send_video(
        self,
        chat_id: str,
        video_data: bytes,
        filename: str = "video.mp4",
        caption: str = "",
    ) -> None:
        """Send a video file via /api/sendFile."""
        await self._send_file(
            chat_id, video_data, "video/mp4", filename, caption, timeout=60.0
        )

    async def send_document(
        self,
        chat_id: str,
        doc_data: bytes,
        filename: str = "document",
        caption: str = "",
    ) -> None:
        """Send a document file via /api/sendFile."""
        await self._send_file(
            chat_id, doc_data, "application/octet-stream", filename, caption
        )

    async def send_voice(
        self,
        chat_id: str,
        audio_data: bytes,
    ) -> None:
        """Send a voice message (PTT) via /api/sendVoice."""
        url = f"{self._base_url}{_SEND_VOICE_PATH}"
        b64 = base64.b64encode(audio_data).decode()
        payload = {
            "chatId": self._chat_id_to_jid(chat_id),
            "file": {
                "mimetype": "audio/ogg; codecs=opus",
                "data": b64,
            },
            "session": self._session,
        }
        try:
            client = self._get_client()
            resp = await client.post(url, json=payload, timeout=30.0)
            if resp.status_code >= 400:
                logger.error("sendVoice %s — %s", resp.status_code, resp.text[:500])
            resp.raise_for_status()
            logger.info("Sent voice for chat_id=%s (%d bytes)", chat_id, len(audio_data))
        except Exception:
            logger.exception("send_voice failed for chat_id=%s", chat_id)
            raise

    async def send_recording(self, chat_id: str, active: bool) -> None:
        """Start or stop the 'recording audio' indicator."""
        path = _START_RECORDING_PATH if active else _STOP_RECORDING_PATH
        url = f"{self._base_url}{path}"
        payload = {
            "chatId": self._chat_id_to_jid(chat_id),
            "session": self._session,
        }
        try:
            client = self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception:
            logger.warning(
                "send_recording(active=%s) failed for chat_id=%s — ignored",
                active, chat_id,
            )

    async def send_seen(self, chat_id: str) -> None:
        """Mark messages as seen (blue ticks) before responding."""
        url = f"{self._base_url}{_SEND_SEEN_PATH}"
        payload = {
            "chatId": self._chat_id_to_jid(chat_id),
            "session": self._session,
        }
        try:
            client = self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception:
            logger.warning("send_seen failed for chat_id=%s — ignored", chat_id)

    async def send_typing(self, chat_id: str, active: bool) -> None:
        """Start or stop the typing indicator (non-critical, no retry)."""
        path = _START_TYPING_PATH if active else _STOP_TYPING_PATH
        url = f"{self._base_url}{path}"
        payload = {
            "chatId": self._chat_id_to_jid(chat_id),
            "session": self._session,
        }
        try:
            client = self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception:
            logger.warning(
                "send_typing(active=%s) failed for chat_id=%s — ignored",
                active,
                chat_id,
            )

    async def _send_file(
        self,
        chat_id: str,
        data: bytes,
        mimetype: str,
        filename: str,
        caption: str = "",
        timeout: float = None,
    ) -> None:
        """Internal: send any file type via /api/sendFile."""
        url = f"{self._base_url}{_SEND_FILE_PATH}"
        b64 = base64.b64encode(data).decode()
        payload = {
            "chatId": self._chat_id_to_jid(chat_id),
            "file": {
                "mimetype": mimetype,
                "filename": filename,
                "data": b64,
            },
            "session": self._session,
        }
        if caption:
            payload["caption"] = caption

        try:
            client = self._get_client()
            resp = await client.post(url, json=payload, timeout=timeout or self._timeout)
            if resp.status_code >= 400:
                logger.error(
                    "sendFile %s — body: %s",
                    resp.status_code, resp.text[:500],
                )
            resp.raise_for_status()
            logger.info(
                "Sent %s for chat_id=%s (%d bytes)",
                mimetype, chat_id, len(data),
            )
        except Exception:
            logger.exception(
                "send_file failed for chat_id=%s mimetype=%s", chat_id, mimetype
            )
            raise
