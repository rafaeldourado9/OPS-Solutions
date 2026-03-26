"""
OllamaAdapter — LLMPort implementation using the local Ollama API.

Ollama exposes an OpenAI-compatible /api/chat endpoint that supports
streaming via newline-delimited JSON (NDJSON).
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncIterator, Optional

import httpx

from core.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMPort):
    """
    LLMPort adapter for Ollama local models.

    Args:
        model_name:   Ollama model tag (e.g. "llama3.1:8b").
        temperature:  Sampling temperature.
        max_tokens:   Maximum output tokens (num_predict in Ollama).
        base_url:     Ollama server URL; falls back to OLLAMA_URL env var.
        timeout:      HTTP request timeout in seconds.
    """

    def __init__(
        self,
        model_name: str = "llama3.1:8b",
        temperature: float = 0.3,
        max_tokens: int = 400,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        num_ctx: int = 4096,
        keep_alive: str = "24h",
    ) -> None:
        self._model_name = model_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._base_url = (base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self._timeout = timeout
        self._num_ctx = num_ctx
        self._keep_alive = keep_alive
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return the shared AsyncClient, creating it lazily."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=50,
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

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        system: str,
        stream: bool,
    ) -> dict:
        """Build the request body for the Ollama /api/chat endpoint."""
        all_messages: list[dict[str, str]] = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        return {
            "model": self._model_name,
            "messages": all_messages,
            "stream": stream,
            "keep_alive": self._keep_alive,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
                "num_ctx": self._num_ctx,
            },
        }

    async def stream_response(
        self,
        messages: list[dict[str, str]],
        system: str = "",
    ) -> AsyncIterator[str]:
        """Stream response chunks from Ollama via NDJSON."""
        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, system, stream=True)

        try:
            client = self._get_client()
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break
        except Exception:
            logger.exception(
                "Ollama stream_response failed for model=%s url=%s",
                self._model_name,
                url,
            )
            raise

    async def generate(
        self,
        messages: list[dict[str, str]],
        system: str = "",
    ) -> str:
        """Generate a complete (non-streaming) response from Ollama."""
        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, system, stream=False)

        try:
            client = self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception:
            logger.exception(
                "Ollama generate failed for model=%s url=%s",
                self._model_name,
                url,
            )
            raise

    async def call_with_tools(
        self,
        messages: list[dict],
        system: str,
        tools: list[dict],
    ) -> dict:
        """
        Non-streaming call with tool support.

        Returns either:
          {"type": "text",      "content": "..."}
          {"type": "tool_call", "id": "...", "name": "...", "args": {...}}
        """
        url = f"{self._base_url}/api/chat"
        all_messages: list[dict] = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        payload = {
            "model": self._model_name,
            "messages": all_messages,
            "tools": tools,
            "stream": False,
            "keep_alive": self._keep_alive,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
                "num_ctx": self._num_ctx,
            },
        }

        try:
            client = self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            msg = data.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            if tool_calls:
                tc = tool_calls[0]
                func = tc.get("function", {})
                args = func.get("arguments", {})
                # Ollama may return arguments as a JSON string
                if isinstance(args, str):
                    try:
                        import json as _json
                        args = _json.loads(args)
                    except Exception:
                        args = {}
                return {
                    "type": "tool_call",
                    "id": tc.get("id", f"call_ollama_{id(tc)}"),
                    "name": func.get("name", ""),
                    "args": args,
                }

            return {"type": "text", "content": msg.get("content", "")}

        except Exception:
            logger.exception(
                "Ollama call_with_tools failed for model=%s", self._model_name
            )
            raise


# ---------------------------------------------------------------------------
# Embedding helper (used by Qdrant adapter, not part of LLMPort)
# ---------------------------------------------------------------------------


async def get_embedding(
    text: str,
    model: str = "nomic-embed-text",
    base_url: Optional[str] = None,
) -> list[float]:
    """
    Generate a text embedding using the Ollama embedding API.

    Tries the new /api/embed endpoint first (Ollama >= 0.1.26),
    then falls back to the legacy /api/embeddings endpoint.

    Args:
        text:     Input text to embed.
        model:    Ollama embedding model name.
        base_url: Override OLLAMA_URL env var.

    Returns:
        List of floats representing the embedding vector.
    """
    url_base = (base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")

    client = _get_embedding_client()
    # Try new endpoint first (Ollama >= 0.1.26)
    try:
        resp = await client.post(
            f"{url_base}/api/embed",
            json={"model": model, "input": text},
        )
        if resp.status_code == 200:
            data = resp.json()
            # New API returns {"embeddings": [[...]]}
            embeddings = data.get("embeddings")
            if embeddings and isinstance(embeddings, list) and embeddings[0]:
                return embeddings[0]
    except Exception:
        pass

    # Fall back to legacy endpoint (Ollama < 0.1.26)
    resp = await client.post(
        f"{url_base}/api/embeddings",
        json={"model": model, "prompt": text},
    )
    resp.raise_for_status()
    return resp.json().get("embedding", [])


_embedding_client: Optional[httpx.AsyncClient] = None


def _get_embedding_client() -> httpx.AsyncClient:
    """Shared client for embedding requests."""
    global _embedding_client
    if _embedding_client is None or _embedding_client.is_closed:
        _embedding_client = httpx.AsyncClient(
            timeout=60.0,
            limits=httpx.Limits(
                max_connections=30,
                max_keepalive_connections=10,
                keepalive_expiry=30,
            ),
        )
    return _embedding_client
