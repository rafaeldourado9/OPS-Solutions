"""
GeminiAdapter — LLMPort implementation using Google Generative AI.

Uses the google-generativeai SDK with async streaming support.
The system prompt is passed as system_instruction to the model.

Dynamic API key: before each LLM call, the adapter checks
/app/shared-agents/.gemini_key (written by the CRM when the user
saves the key in Settings).  If the key changed, genai is reconfigured
and the circuit breaker is reset — no container restart required.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import AsyncIterator, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from core.ports.llm_port import LLMPort
from infrastructure.circuit_breaker import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)

# Path where the CRM writes the Gemini API key at runtime.
_SHARED_KEY_FILE = Path(os.environ.get("SHARED_GEMINI_KEY_FILE", "/app/shared-agents/.gemini_key"))

_default_breaker = CircuitBreaker(
    name="gemini",
    failure_threshold=3,
    recovery_timeout=60.0,
)


def _read_shared_key() -> str:
    """Return the key from the shared file, or '' if missing/unreadable."""
    try:
        if _SHARED_KEY_FILE.exists():
            key = _SHARED_KEY_FILE.read_text().strip()
            if key:
                return key
    except Exception:
        pass
    return ""


class GeminiAdapter(LLMPort):
    """
    LLMPort adapter for Google Gemini models.

    Args:
        model_name:   Gemini model identifier (e.g. "gemini-2.0-flash").
        temperature:  Sampling temperature (0.0–1.0).
        max_tokens:   Maximum output tokens per response.
        api_key:      Initial Gemini API key; updated dynamically from
                      shared file on every call.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 400,
        api_key: Optional[str] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        # Resolve initial key: shared file > argument > env var
        resolved_key = _read_shared_key() or api_key or os.environ.get("GEMINI_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var, pass api_key, "
                "or write the key to the shared file."
            )
        self._api_key = resolved_key
        genai.configure(api_key=resolved_key)
        self._model_name = model_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        self._breaker = circuit_breaker or _default_breaker

    def _refresh_key(self) -> None:
        """
        Check shared file for a newer key.  If changed, reconfigure genai
        and reset the circuit breaker so the new key gets a clean slate.
        """
        latest = _read_shared_key() or os.environ.get("GEMINI_API_KEY", "")
        if latest and latest != self._api_key:
            logger.info("Gemini API key updated from shared file — reconfiguring and resetting circuit breaker")
            self._api_key = latest
            genai.configure(api_key=latest)
            self._breaker.reset()

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
                tool_calls = msg.get("tool_calls") or []
                if tool_calls and not content:
                    tc = tool_calls[0].get("function", {})
                    content = f"Vou consultar {tc.get('name', 'uma fonte')} para responder."
                gemini_messages.append({"role": "model", "parts": [content]})

            elif role == "tool":
                gemini_messages.append({"role": "user", "parts": [content]})

            elif role == "system":
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
        self._refresh_key()
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
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                },
                stream=False,
            )
            try:
                return response.text or ""
            except ValueError:
                finish = None
                if response.candidates:
                    finish = response.candidates[0].finish_reason
                logger.warning("Gemini response blocked/empty for model=%s finish_reason=%s", self._model_name, finish)
                return ""
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
        self._refresh_key()
        try:
            from google.generativeai.types import FunctionDeclaration, Tool as GeminiTool

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
