"""
NullCRMAdapter — CRMPort no-op implementation.

Used when CRM integration is disabled (crm.enabled: false in business.yml)
or when the agent is deployed without CRM.  All events are silently dropped.
"""

from __future__ import annotations

import logging

from core.ports.crm_port import CRMEvent, CRMPort

logger = logging.getLogger(__name__)


class NullCRMAdapter(CRMPort):
    """CRMPort implementation that discards all events."""

    async def push_event(self, event: CRMEvent) -> None:
        logger.debug(
            "NullCRMAdapter: dropped event type=%s chat_id=%s",
            event.event_type,
            event.chat_id,
        )
