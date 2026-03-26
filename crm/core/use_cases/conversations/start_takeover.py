from datetime import datetime
from uuid import UUID

import structlog

from core.ports.outbound.cache_port import CachePort
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.notification_port import NotificationPort

logger = structlog.get_logger()

TAKEOVER_KEY_PREFIX = "takeover:"
TAKEOVER_TTL_SECONDS = 4 * 60 * 60  # 4 hours


class StartTakeoverUseCase:
    """Operator takes over a conversation — agent stops receiving messages."""

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
        self, tenant_id: UUID, chat_id: str, operator_id: UUID, gateway_session: str = "default",
    ) -> None:
        conversation = await self._conversation_repo.get_by_chat_id(tenant_id, chat_id)
        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.is_takeover_active:
            raise ValueError("Takeover already active")

        # Set Redis key so gateway proxy intercepts messages
        takeover_key = f"{TAKEOVER_KEY_PREFIX}{gateway_session}:{chat_id}"
        await self._cache.set(takeover_key, str(operator_id), ttl_seconds=TAKEOVER_TTL_SECONDS)

        # Update conversation
        now = datetime.utcnow()
        conversation.is_takeover_active = True
        conversation.takeover_operator_id = operator_id
        conversation.updated_at = now
        await self._conversation_repo.update(conversation)

        logger.info("takeover_started", chat_id=chat_id, operator_id=str(operator_id))

        # Push WebSocket event
        await self._notification.push_to_tenant(
            tenant_id,
            "takeover_started",
            {
                "chat_id": chat_id,
                "conversation_id": str(conversation.id),
                "operator_id": str(operator_id),
            },
        )
