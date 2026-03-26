"""
GeminiAdapter — LLMPort implementation using Google Generative AI.

Uses the google-generativeai SDK with async streaming support.
The system prompt is passed as system_instruction to the model.
"""

from __future__ import annotations

import logging
import os
from typing import AsyncIterator, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from core.ports.llm_port import LLMPort
from infrastructure.circuit_breaker import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)

# One shared circuit breaker per adapter instance is the norm, but a
# module-level default makes it easy to share across multiple instances.
_default_breaker = CircuitBreaker(
    name="gemini",
    failure_threshold=3,
    recovery_timeout=60.0,
)


class GeminiAdapter(LLMPort):
    """
    LLMPort adapter for Google Gemini models.

    Args:
        model_name:   Gemini model identifier (e.g. "gemini-3-flash-preview").
        temperature:  Sampling temperature (0.0–1.0).
        max_tokens:   Maximum output tokens per response.
        api_key:      Gemini API key; falls back to GEMINI_API_KEY env var.
    """

    def __init__(
        self,
        model_name: str = "gemini-3-flash-preview",
        temperature: float = 0.3,
        max_tokens: int = 400,
        api_key: Optional[str] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var or pass api_key."
            )
        genai.configure(api_key=resolved_key)
        self._model_name = model_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        self._breaker = circuit_breaker or _default_breaker

    def _get_model(self, system: str = "") -> genai.GenerativeModel:
        """Return a configured GenerativeModel, optionally with a system instruction."""
        kwargs: dict = {"model_name": self._model_name}
        if system:
            kwargs["system_instruction"] = system
        return genai.GenerativeModel(**kwargs)

    @staticmethod
    def _to_gemini_messages(messages: list[dict]) -> list[dict]:
        """
        Convert OpenAI-style messages to Gemini's format.

        Gemini uses "user" and "model" roles (not "assistant").
        Tool call/result messages are collapsed into user turns so Gemini
        can follow the tool-use context without native function calling.
        """
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content") or ""

            if role == "assistant":
                # May have tool_calls — flatten to natural text for Gemini
                # so it doesn't echo raw syntax back to the user.
                tool_calls = msg.get("tool_calls") or []
                if tool_calls and not content:
                    tc = tool_calls[0].get("function", {})
                    content = f"Vou consultar {tc.get('name', 'uma fonte')} para responder."
                gemini_messages.append({"role": "model", "parts": [content]})

            elif role == "tool":
                # Tool result — present as user context, not echoed
                gemini_messages.append({
                    "role": "user",
                    "parts": [
                        content
                    ],
                })

            elif role == "system":
                # Handled via system_instruction; skip here.
                continue

            else:
                gemini_messages.append({"role": "user", "parts": [content]})

        return gemini_messages

    async def stream_response(
        self,
        messages: list[dict[str, str]],
        system: str = "",
    ) -> AsyncIterator[str]:
        """Stream response chunks from Gemini, protected by circuit breaker."""
        # Collect full response through breaker, then yield chunks
        # (circuit breaker wraps the whole call, not individual chunks)
        response_text = await self._breaker.call(self.generate, messages, system)
        yield response_text

    async def generate(
        self,
        messages: list[dict],
        system: str = "",
    ) -> str:
        """Generate a complete (non-streaming) response from Gemini."""
        model = self._get_model(system)
        gemini_messages = self._to_gemini_messages(messages)

        try:
            response = await model.generate_content_async(
                contents=gemini_messages,
                generation_config=self._generation_config,
                stream=False,
            )
            return response.text or ""
        except Exception:
            logger.exception("Gemini generate failed for model=%s", self._model_name)
            raise

    async def call_with_tools(
        self,
        messages: list[dict],
        system: str,
        tools: list[dict],
    ) -> dict:
        """
        Non-streaming call with Gemini native function calling.

        Returns either:
          {"type": "text",      "content": "..."}
          {"type": "tool_call", "id": "...", "name": "...", "args": {...}}
        """
        try:
            from google.generativeai.types import FunctionDeclaration, Tool as GeminiTool

            # Convert OpenAI tool format → Gemini FunctionDeclaration
            declarations = []
            for tool in tools:
                func = tool.get("function", {})
                params = func.get("parameters", {})
                declarations.append(
                    FunctionDeclaration(
                        name=func["name"],
                        description=func.get("description", ""),
                        parameters=params,
                    )
                )

            model = self._get_model(system)
            gemini_messages = self._to_gemini_messages(messages)

            response = await model.generate_content_async(
                contents=gemini_messages,
                tools=[GeminiTool(function_declarations=declarations)],
                generation_config=self._generation_config,
                stream=False,
            )

            # Check for function call in response parts
            for candidate in response.candidates or []:
                for part in candidate.content.parts or []:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        return {
                            "type": "tool_call",
                            "id": f"call_gemini_{fc.name}",
                            "name": fc.name,
                            "args": dict(fc.args) if fc.args else {},
                        }

            return {"type": "text", "content": response.text or ""}

        except Exception:
            logger.exception("Gemini call_with_tools failed for model=%s", self._model_name)
            raise
