"""
CRMEventAdapter — CRMPort implementation that POSTs events to a webhook URL.

Fire-and-forget: the caller never sees network errors from this adapter.
Failures are logged and silently swallowed per the CRMPort contract.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from core.ports.crm_port import CRMEvent, CRMPort
from infrastructure.retry import retry

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class CRMEventAdapter(CRMPort):
    """
    CRMPort adapter that forwards events to an external webhook URL.

    Args:
        webhook_url: The HTTP(S) endpoint that accepts CRM event payloads.
    """

    def __init__(self, webhook_url: str) -> None:
        if not webhook_url:
            raise ValueError("webhook_url must not be empty for CRMEventAdapter.")
        self._webhook_url = webhook_url

    async def push_event(self, event: CRMEvent) -> None:
        """POST the event to the configured webhook URL. Never raises."""
        payload = {
            "event_type": event.event_type,
            "chat_id": event.chat_id,
            "agent_id": event.agent_id,
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
        }
        try:
            await retry(
                self._post,
                payload,
                max_retries=2,
                base_delay=1.0,
            )
        except Exception:
            logger.exception(
                "CRM push_event failed after retries for event_type=%s chat_id=%s",
                event.event_type,
                event.chat_id,
            )

    async def _post(self, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(self._webhook_url, json=payload)
            if response.status_code >= 400:
                logger.warning(
                    "CRM webhook returned %d for event_type=%s",
                    response.status_code,
                    payload.get("event_type"),
                )
                # Treat 5xx as retryable; 4xx as permanent
                if response.status_code >= 500:
                    response.raise_for_status()
