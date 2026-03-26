import structlog

from core.domain.events import InboundAgentEvent
from core.use_cases.conversations.store_agent_event_message import StoreAgentEventMessageUseCase
from core.use_cases.customers.sync_from_agent_event import SyncCustomerFromAgentEventUseCase

logger = structlog.get_logger()


class ReceiveAgentEventUseCase:
    """Routes inbound agent events to the appropriate handler."""

    def __init__(
        self,
        sync_customer_uc: SyncCustomerFromAgentEventUseCase,
        store_message_uc: StoreAgentEventMessageUseCase,
    ) -> None:
        self._sync_customer = sync_customer_uc
        self._store_message = store_message_uc

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
            # Could update conversation status, but for now just log
            logger.info("conversation_closed", chat_id=event.chat_id)

        else:
            logger.warning("unknown_agent_event_type", event_type=event.event_type)
