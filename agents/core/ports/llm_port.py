"""
LLMPort — abstract interface for language model adapters.

Any adapter (Gemini, Ollama, OpenAI, …) must implement this interface.
The core layer only imports this file — never a concrete adapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class LLMPort(ABC):
    """Abstract port for language model interactions."""

    @abstractmethod
    async def stream_response(
        self,
        messages: list[dict[str, str]],
        system: str = "",
    ) -> AsyncIterator[str]:
        """
        Stream the LLM response token by token (or chunk by chunk).

        Args:
            messages: Conversation history in OpenAI-style format:
                      [{"role": "user"|"assistant", "content": "..."}]
            system:   System prompt injected before the messages.

        Yields:
            Text chunks as they arrive from the model.
        """
        # Make the method a proper async generator at the abstract level.
        # Subclasses should use `yield` inside their implementation.
        raise NotImplementedError
        yield  # pragma: no cover — keeps mypy happy with AsyncIterator type

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        system: str = "",
    ) -> str:
        """
        Generate a complete response (non-streaming).

        Args:
            messages: Conversation history in OpenAI-style format.
            system:   System prompt.

        Returns:
            The full response text.
        """
        ...
