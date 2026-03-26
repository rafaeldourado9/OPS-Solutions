"""
GatewayPort — abstract interface for WhatsApp (or any messaging) gateways.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class GatewayPort(ABC):
    """Abstract port for sending messages through the messaging gateway."""

    @abstractmethod
    async def send_message(self, chat_id: str, text: str) -> None:
        """
        Send a text message to the specified chat.

        Args:
            chat_id: WhatsApp JID or phone number with @c.us / @g.us suffix.
            text:    Plain text content to send.
        """
        ...

    @abstractmethod
    async def send_typing(self, chat_id: str, active: bool) -> None:
        """
        Start or stop the typing indicator for the specified chat.

        Args:
            chat_id: WhatsApp JID.
            active:  True to start typing, False to stop.
        """
        ...

    async def send_image(
        self,
        chat_id: str,
        image_data: bytes,
        filename: str = "image.jpg",
        caption: str = "",
    ) -> None:
        """
        Send an image to a chat. Optional capability — no-op by default.

        Args:
            chat_id:    WhatsApp JID.
            image_data: Raw image bytes (JPEG/PNG).
            filename:   File name shown in WhatsApp.
            caption:    Optional caption text.
        """
        pass

    async def send_audio(
        self,
        chat_id: str,
        audio_data: bytes,
        filename: str = "audio.ogg",
    ) -> None:
        """
        Send an audio file (voice message) to a chat. Optional — no-op by default.

        Args:
            chat_id:    WhatsApp JID.
            audio_data: Raw audio bytes (OGG Opus preferred for WhatsApp PTT).
            filename:   File name.
        """
        pass

    async def send_video(
        self,
        chat_id: str,
        video_data: bytes,
        filename: str = "video.mp4",
        caption: str = "",
    ) -> None:
        """
        Send a video to a chat. Optional — no-op by default.

        Args:
            chat_id:    WhatsApp JID.
            video_data: Raw video bytes (MP4).
            filename:   File name.
            caption:    Optional caption text.
        """
        pass

    async def send_document(
        self,
        chat_id: str,
        doc_data: bytes,
        filename: str = "document",
        caption: str = "",
    ) -> None:
        """
        Send a document to a chat. Optional — no-op by default.

        Args:
            chat_id:  WhatsApp JID.
            doc_data: Raw document bytes.
            filename: File name shown in WhatsApp.
            caption:  Optional caption text.
        """
        pass

    async def send_voice(
        self,
        chat_id: str,
        audio_data: bytes,
    ) -> None:
        """
        Send a voice message (PTT) to a chat. Optional — no-op by default.

        Args:
            chat_id:    WhatsApp JID.
            audio_data: Raw audio bytes (OGG Opus).
        """
        pass

    async def send_recording(self, chat_id: str, active: bool) -> None:
        """
        Start or stop the "recording audio" indicator for the specified chat.

        Shows "recording audio..." in the chat instead of "typing...".
        Should be used when the agent is about to send a voice message.

        Args:
            chat_id: WhatsApp JID.
            active:  True to start recording indicator, False to stop.
        """
        pass

    async def send_seen(self, chat_id: str) -> None:
        """
        Mark messages in the chat as seen (blue ticks). Optional — no-op by default.

        This should be called before typing to simulate a human reading the
        message before starting to respond.

        Args:
            chat_id: WhatsApp JID.
        """
        pass
