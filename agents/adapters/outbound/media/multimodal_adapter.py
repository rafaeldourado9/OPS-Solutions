"""
MultimodalAdapter — MediaPort implementation using Ollama local models.

  Audio (PTT/MP3/OGG): Whisper model via Ollama /api/generate with base64 audio
  Image (PNG/JPG/WEBP): LLaVA model via Ollama /api/chat with base64 image
  Video (MP4/AVI):      Frame extraction via ffmpeg → LLaVA each frame → summary

The Ollama Whisper API accepts audio as base64 in the `audio` field of the
generate endpoint (supported since Ollama 0.5.x with whisper model family).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from core.ports.media_port import MediaPort

logger = logging.getLogger(__name__)

# Prompts
_IMAGE_PROMPT = (
    "Descreva esta imagem em detalhes, focando em informações úteis para "
    "um atendimento comercial: produtos visíveis, texto na imagem, condição "
    "dos itens, contexto da situação."
)

_VIDEO_FRAME_PROMPT = (
    "Descreva este frame de vídeo de forma concisa, focando em elementos "
    "relevantes para atendimento: produtos, pessoas, textos visíveis, contexto."
)

_VIDEO_SUMMARY_PROMPT = (
    "Com base nas descrições dos frames abaixo, forneça um resumo coerente "
    "do conteúdo do vídeo em 2-3 frases:\n\n{frames}"
)


class MultimodalAdapter(MediaPort):
    """
    MediaPort implementation for Whisper (audio) + LLaVA (image/video).

    Args:
        audio_model:        Ollama model for audio transcription (e.g. "whisper:large-v3").
        image_model:        Ollama model for image/video description (e.g. "llava:13b").
        video_frame_interval: Extract 1 frame every N seconds of video.
        ollama_url:         Ollama server URL; falls back to OLLAMA_URL env var.
        timeout:            HTTP timeout for Ollama requests (seconds).
    """

    def __init__(
        self,
        audio_model: str = "whisper:large-v3",
        image_model: str = "llava:13b",
        video_frame_interval: int = 5,
        ollama_url: Optional[str] = None,
        timeout: float = 180.0,
    ) -> None:
        self._audio_model = audio_model
        self._image_model = image_model
        self._video_frame_interval = video_frame_interval
        self._base_url = (
            ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        ).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return the shared AsyncClient, creating it lazily."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=30,
                    max_keepalive_connections=10,
                    keepalive_expiry=30,
                ),
            )
        return self._client

    async def close(self) -> None:
        """Close the shared HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Audio transcription
    # ------------------------------------------------------------------

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio bytes using the Ollama Whisper model.

        WhatsApp PTT arrives as OGG/Opus. Converts to WAV via ffmpeg first
        (if available) since Whisper handles WAV more reliably.
        Returns the transcription text, or an empty string on failure.
        """
        data = await _convert_to_wav(audio_data)
        b64 = base64.b64encode(data).decode()
        payload = {
            "model": self._audio_model,
            "prompt": "",
            "audio": b64,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "").strip()
                if text:
                    logger.info("Whisper transcription: %r", text[:100])
                    return text
                logger.warning("Whisper returned empty response")
        except Exception:
            logger.exception(
                "Whisper transcription failed (model=%s)",
                self._audio_model,
            )

        return ""

    # ------------------------------------------------------------------
    # Image description
    # ------------------------------------------------------------------

    async def describe_image(self, image_data: bytes) -> str:
        """
        Describe an image using LLaVA via Ollama chat endpoint.

        Returns the description text, or an empty string on failure.
        """
        b64 = base64.b64encode(image_data).decode()
        payload = {
            "model": self._image_model,
            "messages": [
                {
                    "role": "user",
                    "content": _IMAGE_PROMPT,
                    "images": [b64],
                }
            ],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except Exception:
            logger.exception(
                "LLaVA image description failed (model=%s)", self._image_model
            )
            return ""

    # ------------------------------------------------------------------
    # Video description
    # ------------------------------------------------------------------

    async def describe_video(self, video_data: bytes) -> str:
        """
        Describe a video by extracting frames and running LLaVA on each.

        Requires ffmpeg to be installed and available on PATH.
        Falls back to a placeholder message if ffmpeg is unavailable.
        """
        frames = await _extract_frames(video_data, self._video_frame_interval)
        if not frames:
            logger.warning("No frames extracted from video — ffmpeg may be unavailable")
            return ""

        logger.info("Describing %d video frame(s) with LLaVA", len(frames))

        # Describe each frame concurrently (with a limit to avoid memory pressure)
        semaphore = asyncio.Semaphore(3)

        async def _describe_frame(frame_bytes: bytes) -> str:
            async with semaphore:
                return await self._describe_frame(frame_bytes)

        descriptions = await asyncio.gather(
            *[_describe_frame(f) for f in frames],
            return_exceptions=True,
        )

        valid = [d for d in descriptions if isinstance(d, str) and d.strip()]
        if not valid:
            return ""

        if len(valid) == 1:
            return valid[0]

        # Summarise multiple frame descriptions
        frames_text = "\n".join(f"Frame {i+1}: {d}" for i, d in enumerate(valid))
        return await self._summarise_frames(frames_text)

    async def _describe_frame(self, image_data: bytes) -> str:
        """Describe a single extracted video frame."""
        b64 = base64.b64encode(image_data).decode()
        payload = {
            "model": self._image_model,
            "messages": [
                {
                    "role": "user",
                    "content": _VIDEO_FRAME_PROMPT,
                    "images": [b64],
                }
            ],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "").strip()
        except Exception:
            logger.exception("Frame description failed")
            return ""

    async def _summarise_frames(self, frames_text: str) -> str:
        """Use LLaVA (text-only) to summarise multiple frame descriptions."""
        prompt = _VIDEO_SUMMARY_PROMPT.format(frames=frames_text)
        payload = {
            "model": self._image_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "").strip()
        except Exception:
            logger.exception("Frame summary failed — returning concatenated descriptions")
            return frames_text


# ---------------------------------------------------------------------------
# Audio conversion — OGG/Opus → WAV for Whisper compatibility
# ---------------------------------------------------------------------------


async def _convert_to_wav(audio_data: bytes) -> bytes:
    """
    Convert audio bytes to WAV using ffmpeg (runs in thread pool).
    Falls back to original bytes if ffmpeg is unavailable.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _convert_to_wav_sync, audio_data)


def _convert_to_wav_sync(audio_data: bytes) -> bytes:
    """Synchronous OGG→WAV conversion via ffmpeg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_file = tmp / "input.ogg"
        output_file = tmp / "output.wav"
        input_file.write_bytes(audio_data)
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(input_file),
                    "-ar", "16000",   # 16kHz — Whisper's native rate
                    "-ac", "1",       # mono
                    "-f", "wav",
                    str(output_file),
                    "-loglevel", "error",
                ],
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0 and output_file.exists():
                return output_file.read_bytes()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return audio_data  # fallback: original bytes


# ---------------------------------------------------------------------------
# Frame extraction via ffmpeg subprocess
# ---------------------------------------------------------------------------


async def _extract_frames(
    video_data: bytes,
    interval_seconds: int,
) -> list[bytes]:
    """
    Extract frames from video bytes at regular intervals using ffmpeg.

    Runs ffmpeg in a thread pool to avoid blocking the event loop.
    Returns list of PNG image bytes (one per extracted frame).
    Returns [] if ffmpeg is unavailable or extraction fails.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_frames_sync, video_data, interval_seconds)


def _extract_frames_sync(video_data: bytes, interval_seconds: int) -> list[bytes]:
    """Synchronous frame extraction — runs in thread pool."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        video_file = tmp_path / "input.mp4"
        video_file.write_bytes(video_data)

        output_pattern = str(tmp_path / "frame_%04d.png")
        cmd = [
            "ffmpeg",
            "-i", str(video_file),
            "-vf", f"fps=1/{interval_seconds}",
            "-q:v", "2",
            output_pattern,
            "-y",
            "-loglevel", "error",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.warning(
                    "ffmpeg exited with code %d: %s",
                    result.returncode,
                    result.stderr.decode(errors="replace"),
                )
                return []
        except FileNotFoundError:
            logger.warning("ffmpeg not found on PATH — video frame extraction unavailable")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg timed out during frame extraction")
            return []

        frames = sorted(tmp_path.glob("frame_*.png"))
        return [f.read_bytes() for f in frames]
