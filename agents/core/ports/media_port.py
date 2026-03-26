"""
MediaPort — abstract interface for multimodal media processing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class MediaPort(ABC):
    """Abstract port for audio transcription and visual description."""

    @abstractmethod
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe an audio file to text.

        Args:
            audio_data: Raw bytes of the audio file (OGG, MP3, WAV, …).

        Returns:
            Transcription text.
        """
        ...

    @abstractmethod
    async def describe_image(self, image_data: bytes) -> str:
        """
        Produce a detailed textual description of an image.

        Args:
            image_data: Raw bytes of the image (JPEG, PNG, WEBP, …).

        Returns:
            Human-readable description of the image contents.
        """
        ...

    @abstractmethod
    async def describe_video(self, video_data: bytes) -> str:
        """
        Produce a summary description of a video by sampling frames.

        Args:
            video_data: Raw bytes of the video file (MP4, AVI, …).

        Returns:
            Human-readable summary combining descriptions of sampled frames.
        """
        ...

    async def generate_image(self, prompt: str) -> "Optional[bytes]":
        """
        Generate an image from a text prompt.

        Optional capability — returns None by default.
        Implementations that support image generation should override this.

        Args:
            prompt: Text description of the image to generate (English works best).

        Returns:
            Raw image bytes (JPEG/PNG), or None if not supported / failed.
        """
        return None

    async def synthesize_speech(
        self, text: str, voice: str = "", voice_clone_sample: str = "",
    ) -> "Optional[bytes]":
        """
        Convert text to speech audio.

        Optional capability — returns None by default.
        Implementations that support TTS should override this.

        Args:
            text:  Text to speak.
            voice: Voice name/ID (implementation-specific, used as fallback).
            voice_clone_sample: Path to an audio file for voice cloning.
                                When provided, the TTS engine clones that voice
                                instead of using a prebuilt voice.

        Returns:
            Raw audio bytes (OGG/MP3), or None if not supported / failed.
        """
        return None
