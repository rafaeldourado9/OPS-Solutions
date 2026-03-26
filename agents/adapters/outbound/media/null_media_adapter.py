"""
NullMediaAdapter — MediaPort no-op implementation.

Used in tests and when media processing is disabled.
All methods return empty strings — the caller handles the empty case gracefully.
"""

from __future__ import annotations

import logging

from core.ports.media_port import MediaPort

logger = logging.getLogger(__name__)


class NullMediaAdapter(MediaPort):
    """MediaPort implementation that does nothing."""

    async def transcribe_audio(self, audio_data: bytes) -> str:
        logger.debug("NullMediaAdapter: skipping audio transcription (%d bytes)", len(audio_data))
        return ""

    async def describe_image(self, image_data: bytes) -> str:
        logger.debug("NullMediaAdapter: skipping image description (%d bytes)", len(image_data))
        return ""

    async def describe_video(self, video_data: bytes) -> str:
        logger.debug("NullMediaAdapter: skipping video description (%d bytes)", len(video_data))
        return ""
