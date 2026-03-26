"""
GeminiMediaAdapter — MediaPort implementation using Google Gemini for all media.

Audio:  Gemini native audio understanding (upload file → transcribe)
Image:  Gemini Vision with inline base64 (no Ollama/LLaVA needed)
Video:  Gemini Files API upload → video understanding
Image generation: Gemini image generation via REST API
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import google.generativeai as genai
import httpx

from core.ports.media_port import MediaPort

logger = logging.getLogger(__name__)

# Prompts (Portuguese context for commercial support)
_AUDIO_PROMPT = (
    "Transcreva este áudio em português brasileiro. "
    "Retorne APENAS o texto falado, sem comentários ou formatação."
)

_IMAGE_PROMPT = (
    "Descreva esta imagem em detalhes, focando em informações úteis para "
    "um atendimento comercial: produtos visíveis, texto na imagem, condição "
    "dos itens, contexto da situação. Responda em português brasileiro."
)

_VIDEO_PROMPT = (
    "Descreva este vídeo em detalhes, focando em informações relevantes para "
    "um atendimento comercial: o que acontece, produtos, pessoas, textos visíveis. "
    "Responda em português brasileiro em 3-5 frases."
)

# MIME type detection for inline image data
_MIME_BY_EXT = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",   # webp starts with RIFF
    b"GIF8": "image/gif",
}


def _detect_image_mime(data: bytes) -> str:
    """Detect image MIME type from magic bytes."""
    for magic, mime in _MIME_BY_EXT.items():
        if data[:len(magic)] == magic:
            return mime
    return "image/jpeg"  # safe default


class GeminiMediaAdapter(MediaPort):
    """
    MediaPort implementation using Google Gemini for all media types.

    Args:
        audio_model:          Gemini model for audio transcription.
        image_model:          Gemini model for image/video description.
        video_model:          Gemini model for video understanding (defaults to image_model).
        video_frame_interval: Not used (kept for config compat).
        timeout:              HTTP timeout for direct API calls (seconds).
        api_key:              Gemini API key; falls back to GEMINI_API_KEY env var.
    """

    def __init__(
        self,
        audio_model: str = "gemini-3-flash-preview",
        image_model: str = "gemini-3-flash-preview",
        video_model: Optional[str] = None,
        video_frame_interval: int = 5,
        timeout: float = 180.0,
        api_key: Optional[str] = None,
    ) -> None:
        self._audio_model = audio_model
        self._image_model = image_model
        self._video_model = video_model or image_model
        self._timeout = timeout

        resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not resolved_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY env var.")
        self._api_key = resolved_key
        genai.configure(api_key=resolved_key)

    # ------------------------------------------------------------------
    # Audio transcription
    # ------------------------------------------------------------------

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio bytes using Gemini's native audio understanding.

        Converts to WAV first (better compatibility); falls back to raw bytes
        if ffmpeg is unavailable.
        """
        wav_data = await _convert_to_wav(audio_data)

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._transcribe_sync, wav_data)
        except Exception:
            logger.exception("Gemini audio transcription failed")
            return ""

    def _transcribe_sync(self, audio_data: bytes) -> str:
        suffix = ".wav"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            audio_file = genai.upload_file(tmp_path)

            # Wait for processing
            import time
            for _ in range(30):
                if audio_file.state.name != "PROCESSING":
                    break
                time.sleep(1)
                audio_file = genai.get_file(audio_file.name)

            model = genai.GenerativeModel(self._audio_model)
            response = model.generate_content([_AUDIO_PROMPT, audio_file])

            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass

            text = (response.text or "").strip()
            if text:
                logger.info("Gemini transcription: %r", text[:100])
            else:
                logger.warning("Gemini returned empty transcription")
            return text

        except Exception:
            logger.exception("Gemini audio transcription (sync) failed")
            return ""
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Image description
    # ------------------------------------------------------------------

    async def describe_image(self, image_data: bytes) -> str:
        """
        Describe an image using Gemini Vision (inline base64, no upload needed).
        """
        mime_type = _detect_image_mime(image_data)
        b64 = base64.b64encode(image_data).decode()

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None, self._describe_image_sync, b64, mime_type
            )
        except Exception:
            logger.exception("Gemini image description failed")
            return ""

    def _describe_image_sync(self, b64: str, mime_type: str) -> str:
        try:
            model = genai.GenerativeModel(self._image_model)
            image_part = {"mime_type": mime_type, "data": b64}
            response = model.generate_content([_IMAGE_PROMPT, image_part])
            text = (response.text or "").strip()
            if text:
                logger.info("Gemini image description: %r", text[:100])
            return text
        except Exception:
            logger.exception("Gemini image description (sync) failed")
            return ""

    # ------------------------------------------------------------------
    # Video description
    # ------------------------------------------------------------------

    async def describe_video(self, video_data: bytes) -> str:
        """
        Describe a video using Gemini's video understanding (Files API upload).
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._describe_video_sync, video_data)
        except Exception:
            logger.exception("Gemini video description failed")
            return ""

    def _describe_video_sync(self, video_data: bytes) -> str:
        tmp_path = None
        video_file = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(video_data)
                tmp_path = tmp.name

            logger.info("Uploading video to Gemini Files API (%d bytes)", len(video_data))
            video_file = genai.upload_file(tmp_path, mime_type="video/mp4")

            # Wait for processing
            import time
            for _ in range(60):
                if video_file.state.name != "PROCESSING":
                    break
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                logger.warning("Gemini video processing failed")
                return ""

            model = genai.GenerativeModel(self._video_model)
            response = model.generate_content([video_file, _VIDEO_PROMPT])

            try:
                genai.delete_file(video_file.name)
            except Exception:
                pass

            text = (response.text or "").strip()
            if text:
                logger.info("Gemini video description: %r", text[:100])
            return text

        except Exception:
            logger.exception("Gemini video description (sync) failed")
            if video_file:
                try:
                    genai.delete_file(video_file.name)
                except Exception:
                    pass
            return ""
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Generate an image using Gemini's image generation capability.

        Returns raw image bytes (JPEG/PNG), or None on failure.
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_image_sync, prompt
            )
        except Exception:
            logger.exception("Gemini image generation failed for prompt: %r", prompt[:80])
            return None

    def _generate_image_sync(self, prompt: str) -> Optional[bytes]:
        """Synchronous image generation via Gemini native image output.

        Uses gemini-3-flash-preview-exp with responseModalities: ["IMAGE", "TEXT"]
        for native image generation (diagrams, architecture, flows, etc).
        Falls back to Imagen 3 if native generation fails.
        """
        # Enhance prompt for technical diagrams
        enhanced = (
            f"{prompt}\n\n"
            "Style: clean, professional, high contrast, white background, "
            "clearly labeled components, sharp lines, modern flat design. "
            "If this is an architecture diagram: use boxes for components, "
            "arrows for data flow, color-coded layers."
        )

        # Try gemini-3-flash-preview-exp (native image generation)
        image = self._try_gemini_native_image(enhanced)
        if image:
            return image

        # Fallback: Imagen 3
        logger.info("Gemini native image failed, trying Imagen 3")
        return self._try_imagen3(enhanced)

    def _try_gemini_native_image(self, prompt: str) -> Optional[bytes]:
        """Generate image using Gemini 2.0 Flash native image output."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3-flash-preview-exp:generateContent"
            f"?key={self._api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "temperature": 0.4,
            },
        }
        try:
            import httpx as _httpx
            with _httpx.Client(timeout=90.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        return base64.b64decode(part["inlineData"]["data"])
            logger.warning("Gemini native image: no image data in response")
            return None
        except Exception:
            logger.exception("Gemini native image generation failed")
            return None

    def _try_imagen3(self, prompt: str) -> Optional[bytes]:
        """Fallback: generate image using Imagen 3 API."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"imagen-3.0-generate-002:generateContent"
            f"?key={self._api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
        }
        try:
            import httpx as _httpx
            with _httpx.Client(timeout=90.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        return base64.b64decode(part["inlineData"]["data"])
            logger.warning("Imagen 3: no image data in response")
            return None
        except Exception:
            logger.exception("Imagen 3 image generation failed")
            return None

    # ------------------------------------------------------------------
    # Text-to-Speech (TTS) via Gemini
    # ------------------------------------------------------------------

    # Gemini TTS voices — Portuguese-friendly options
    _TTS_VOICES = ["Kore", "Puck", "Aoede", "Charon", "Fenrir", "Leda"]

    async def synthesize_speech(
        self, text: str, voice: str = "", voice_clone_sample: str = "",
    ) -> Optional[bytes]:
        """
        Convert text to speech using Gemini TTS (prebuilt voices only).

        Voice cloning is handled externally by CoquiTTSAdapter.
        This method is the fallback for prebuilt voices.
        """
        if not text.strip():
            return None
        try:
            raw_audio = await asyncio.get_event_loop().run_in_executor(
                None, self._synthesize_speech_prebuilt, text, voice,
            )
            if raw_audio is None:
                return None
            ogg = await self._convert_to_ogg_opus(raw_audio)
            return ogg
        except Exception:
            logger.exception("TTS synthesis failed for text: %r", text[:80])
            return None

    def _synthesize_speech_prebuilt(self, text: str, voice: str = "") -> Optional[bytes]:
        """Synchronous TTS via Gemini REST API with prebuilt voice."""
        voice_name = voice or "Kore"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash-preview-tts:generateContent"
            f"?key={self._api_key}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": (
                        "Fale o texto a seguir de forma natural e conversacional, "
                        "como se estivesse mandando um áudio no WhatsApp para um amigo. "
                        "Use tom informal, com pausas naturais e ritmo de conversa real. "
                        "Não soe robótico. Fale em português brasileiro. "
                        "IMPORTANTE: fale o texto COMPLETO, do início ao fim. "
                        "Não corte, não resuma, não interrompa. Termine a frase inteira. "
                        "Se o texto for longo, mantenha o ritmo calmo e constante.\n\n"
                        f"{text}"
                    )}],
                },
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_name,
                        }
                    }
                },
            },
        }
        return self._call_tts_api(url, payload)

    def _call_tts_api(self, url: str, payload: dict) -> Optional[bytes]:
        """Send TTS request and extract audio bytes from response."""
        try:
            import httpx as _httpx
            with _httpx.Client(timeout=90.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        audio_b64 = part["inlineData"]["data"]
                        return base64.b64decode(audio_b64)
            logger.warning("Gemini TTS: no audio data in response")
            return None
        except Exception:
            logger.exception("Gemini TTS REST call failed")
            return None

    @staticmethod
    async def _convert_to_ogg_opus(audio_data: bytes) -> bytes:
        """Convert raw audio (PCM/WAV) to OGG Opus for WhatsApp PTT."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _convert_to_ogg_opus_sync, audio_data)


def _convert_to_ogg_opus_sync(audio_data: bytes) -> bytes:
    """Synchronous conversion to OGG Opus via ffmpeg (WhatsApp PTT format).

    Gemini TTS returns raw PCM linear16 at 24kHz mono (no WAV headers),
    so we must specify the input format explicitly.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_file = tmp / "input.pcm"
        output_file = tmp / "output.ogg"
        input_file.write_bytes(audio_data)
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    # Input: raw PCM signed 16-bit little-endian, 24kHz, mono
                    "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", str(input_file),
                    # Output: OGG Opus (WhatsApp PTT format)
                    "-c:a", "libopus", "-b:a", "64k",
                    "-ar", "48000", "-ac", "1",
                    "-application", "voip",
                    str(output_file),
                ],
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and output_file.exists():
                return output_file.read_bytes()
            logger.warning("ffmpeg OGG Opus conversion failed: %s", result.stderr[:200])
        except Exception:
            logger.exception("ffmpeg OGG Opus conversion failed")
        # Fallback: return raw audio
        return audio_data


# ---------------------------------------------------------------------------
# Audio conversion — OGG/Opus → WAV (best effort, falls back to raw bytes)
# ---------------------------------------------------------------------------

async def _convert_to_wav(audio_data: bytes) -> bytes:
    """Convert audio bytes to WAV using ffmpeg (best effort)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _convert_to_wav_sync, audio_data)


def _convert_to_wav_sync(audio_data: bytes) -> bytes:
    """Synchronous OGG/OGA/MP4 → WAV conversion via ffmpeg."""
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
                    "-ar", "16000",
                    "-ac", "1",
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
            logger.debug("ffmpeg not available — sending raw audio to Gemini")
    return audio_data  # Gemini can handle OGG directly in many cases
