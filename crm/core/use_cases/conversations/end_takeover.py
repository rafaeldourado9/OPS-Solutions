from datetime import datetime
from uuid import UUID

import structlog

from core.ports.outbound.cache_port import CachePort
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.notification_port import NotificationPort

logger = structlog.get_logger()

TAKEOVER_KEY_PREFIX = "takeover:"


class EndTakeoverUseCase:
    """Operator releases conversation back to the agent."""

    def __init__(
        self,
        conversation_repo: ConversationRepositoryPort,
        cache: CachePort,
        notification: NotificationPort,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._cache = cache
        self._notification = notification

    async def execute(
        self, tenant_id: UUID, chat_id: str, gateway_session: str = "default",
    ) -> None:
        conversation = await self._conversation_repo.get_by_chat_id(tenant_id, chat_id)
        if not conversation:
            raise ValueError("Conversation not found")

        if not conversation.is_takeover_active:
            raise ValueError("No active takeover")

        # Delete Redis key so gateway proxy resumes forwarding to agent
        takeover_key = f"{TAKEOVER_KEY_PREFIX}{gateway_session}:{chat_id}"
        await self._cache.delete(takeover_key)

        # Update conversation
        now = datetime.utcnow()
        conversation.is_takeover_active = False
        conversation.takeover_operator_id = None
        conversation.updated_at = now
        await self._conversation_repo.update(conversation)

        logger.info("takeover_ended", chat_id=chat_id)

        # Push WebSocket event
        await self._notification.push_to_tenant(
            tenant_id,
            "takeover_ended",
            {
                "chat_id": chat_id,
                "conversation_id": str(conversation.id),
            },
        )
