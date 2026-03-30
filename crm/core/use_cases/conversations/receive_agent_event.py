import asyncio

import httpx
import structlog

from core.domain.events import InboundAgentEvent
from core.ports.outbound.tenant_repository import TenantRepositoryPort
from core.use_cases.conversations.store_agent_event_message import StoreAgentEventMessageUseCase
from core.use_cases.customers.sync_from_agent_event import SyncCustomerFromAgentEventUseCase

logger = structlog.get_logger()


class ReceiveAgentEventUseCase:
    """Routes inbound agent events to the appropriate handler."""

    def __init__(
        self,
        sync_customer_uc: SyncCustomerFromAgentEventUseCase,
        store_message_uc: StoreAgentEventMessageUseCase,
        tenant_repo: TenantRepositoryPort,
    ) -> None:
        self._sync_customer = sync_customer_uc
        self._store_message = store_message_uc
        self._tenant_repo = tenant_repo

    async def execute(self, event: InboundAgentEvent) -> None:
        logger.info(
            "agent_event_received",
            event_type=event.event_type,
            chat_id=event.chat_id,
            agent_id=event.agent_id,
        )

        if event.event_type == "new_contact":
            await self._sync_customer.execute(event)

        elif event.event_type in ("message_received", "agent_response_sent"):
            await self._store_message.execute(event)

        elif event.event_type == "conversation_closed":
            logger.info("conversation_closed", chat_id=event.chat_id)

        else:
            logger.warning("unknown_agent_event_type", event_type=event.event_type)

        # Resolve webhook URL NOW while the DB session is still open.
        # asyncio.create_task runs after the request handler returns (session already
        # committed), so we must NOT use self._tenant_repo inside the background task.
        webhook_url = ""
        tenant_id_str = ""
        try:
            tenant = await self._tenant_repo.get_by_agent_id(event.agent_id)
            if tenant:
                webhook_url = (tenant.raw_settings or {}).get("integrations", {}).get("webhook_url", "")
                tenant_id_str = str(tenant.id)
        except Exception:
            logger.warning("webhook_tenant_lookup_failed", agent_id=event.agent_id)

        if webhook_url:
            asyncio.create_task(self._forward_to_webhook(event, webhook_url, tenant_id_str))

    async def _forward_to_webhook(
        self,
        event: InboundAgentEvent,
        webhook_url: str,
        tenant_id: str,
    ) -> None:
        """Fire-and-forget: POST event to tenant's configured webhook URL.

        NOTE: runs in a background task — must NOT use DB session (already committed).
        All data must be passed as arguments.
        """
        try:
            payload = {
                "event_type": event.event_type,
                "chat_id": event.chat_id,
                "agent_id": event.agent_id,
                "tenant_id": tenant_id,
                "data": event.data,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
                logger.info(
                    "webhook_forwarded",
                    url=webhook_url,
                    event_type=event.event_type,
                    status=resp.status_code,
                )
        except Exception:
            logger.exception("webhook_forward_failed", agent_id=event.agent_id)
