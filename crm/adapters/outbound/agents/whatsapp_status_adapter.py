"""
WhatsApp Status Adapter — proxies to the Baileys gateway with circuit breaker.

Circuit breaker states:
  CLOSED    → normal, requests pass through
  OPEN      → gateway unreachable, reject fast with fallback response
  HALF_OPEN → testing recovery after timeout
"""

from __future__ import annotations

import base64
import io
import os
import time
from enum import Enum
from typing import Any

import httpx


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class WhatsAppStatusAdapter:
    """HTTP client to the Baileys gateway with circuit breaker."""

    def __init__(
        self,
        gateway_url: str | None = None,
        api_key: str | None = None,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ):
        self._url = (gateway_url or os.environ.get("GATEWAY_URL", "http://gateway:3000")).rstrip("/")
        self._api_key = api_key or os.environ.get("GATEWAY_API_KEY") or os.environ.get("WAHA_API_KEY", "")
        self._threshold = failure_threshold
        self._recovery = recovery_timeout

        self._state = CBState.CLOSED
        self._failures = 0
        self._last_failure: float = 0.0

    # ── Circuit breaker helpers ────────────────────────────────────────────────

    def _can_call(self) -> bool:
        if self._state == CBState.CLOSED:
            return True
        if self._state == CBState.OPEN:
            if time.monotonic() - self._last_failure >= self._recovery:
                self._state = CBState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN

    def _success(self) -> None:
        self._state = CBState.CLOSED
        self._failures = 0

    def _failure(self) -> None:
        self._failures += 1
        self._last_failure = time.monotonic()
        if self._failures >= self._threshold:
            self._state = CBState.OPEN

    def _headers(self) -> dict[str, str]:
        if self._api_key:
            return {"X-Api-Key": self._api_key}
        return {}

    # ── Public methods ─────────────────────────────────────────────────────────

    async def get_status(self, session: str | None = None) -> dict[str, Any]:
        """GET /health — returns connection status."""
        if not self._can_call():
            return {
                "status": "unreachable",
                "circuit": self._state,
                "phone": None,
                "uptime": 0,
            }
        try:
            params = {"session": session} if session else {}
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._url}/health", params=params)
                resp.raise_for_status()
                data = resp.json()
                self._success()
                # Baileys gateway returns status:"ok" when connected; normalise for frontend
                raw_status = data.get("status", "")
                normalised = "connected" if raw_status == "ok" else raw_status
                return {**data, "status": normalised, "circuit": self._state}
        except Exception as exc:
            self._failure()
            return {
                "status": "unreachable",
                "circuit": self._state,
                "phone": None,
                "uptime": 0,
                "error": str(exc),
            }

    async def get_qr(self, session: str | None = None) -> dict[str, Any]:
        """GET /api/qr — returns QR code as base64 PNG."""
        if not self._can_call():
            return {"qr": None, "status": "unreachable", "circuit": self._state}
        try:
            params = {"session": session} if session else {}
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._url}/api/qr", headers=self._headers(), params=params
                )
                resp.raise_for_status()
                data = resp.json()
                self._success()

                qr_b64 = None
                if data.get("qr"):
                    import qrcode  # lazy import

                    img = qrcode.make(data["qr"])
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    qr_b64 = "data:image/png;base64," + base64.b64encode(
                        buf.getvalue()
                    ).decode()

                return {
                    "qr": qr_b64,
                    "status": data.get("status", "connected"),
                    "phone": data.get("phone"),
                    "circuit": self._state,
                }
        except Exception as exc:
            self._failure()
            return {
                "qr": None,
                "status": "unreachable",
                "circuit": self._state,
                "error": str(exc),
            }

    async def restart(self, session: str | None = None) -> dict[str, Any]:
        """POST /api/restart — force a reconnect."""
        try:
            params = {"session": session} if session else {}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._url}/api/restart", headers=self._headers(), params=params
                )
                resp.raise_for_status()
                self._success()
                return resp.json()
        except Exception as exc:
            self._failure()
            return {"status": "error", "error": str(exc)}

    async def logout(self, session: str | None = None) -> dict[str, Any]:
        """POST /api/logout — disconnect and clear session."""
        try:
            params = {"session": session} if session else {}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._url}/api/logout", headers=self._headers(), params=params
                )
                resp.raise_for_status()
                self._success()
                return resp.json()
        except Exception as exc:
            self._failure()
            return {"status": "error", "error": str(exc)}

    async def create_session(self, session_name: str) -> dict[str, Any]:
        """POST /api/sessions — create a new gateway session."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._url}/api/sessions",
                    headers=self._headers(),
                    json={"name": session_name},
                )
                resp.raise_for_status()
                self._success()
                return resp.json()
        except Exception as exc:
            self._failure()
            return {"status": "error", "error": str(exc)}

    async def remove_session(self, session_name: str) -> dict[str, Any]:
        """DELETE /api/sessions/:name — remove a gateway session."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(
                    f"{self._url}/api/sessions/{session_name}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                self._success()
                return resp.json()
        except Exception as exc:
            self._failure()
            return {"status": "error", "error": str(exc)}

    async def list_ollama_models(self) -> list[str]:
        """GET Ollama /api/tags — returns available model names."""
        ollama_url = os.environ.get("OLLAMA_URL", "http://ollama:11434").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{ollama_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    @property
    def circuit_state(self) -> CBState:
        return self._state


# Module-level singleton — preserves circuit breaker state across requests
_adapter: WhatsAppStatusAdapter | None = None


def get_whatsapp_adapter() -> WhatsAppStatusAdapter:
    global _adapter
    if _adapter is None:
        _adapter = WhatsAppStatusAdapter()
    return _adapter
