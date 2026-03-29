from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import structlog

from core.domain.conversation import CRMMessage, Conversation
from core.ports.outbound.agent_gateway import AgentGatewayPort
from core.ports.outbound.cache_port import CachePort
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.message_repository import MessageRepositoryPort
from core.ports.outbound.notification_port import NotificationPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort

logger = structlog.get_logger()

TAKEOVER_KEY_PREFIX = "takeover:"


class HandleGatewayProxyUseCase:
    """
    Gateway webhook proxy: intercepts messages for human takeover.

    Flow:
    1. Gateway sends all incoming messages here instead of directly to agents.
    2. Check Redis for takeover state on this chat.
    3. If takeover active: store message + push to WebSocket (operator handles it).
    4. If no takeover: forward raw payload to agents /webhook unchanged.
    """

    def __init__(
        self,
        agent_gateway: AgentGatewayPort,
        cache: CachePort,
        conversation_repo: Optional[ConversationRepositoryPort] = None,
        message_repo: Optional[MessageRepositoryPort] = None,
        tenant_repo: Optional[TenantRepositoryPort] = None,
        notification: Optional[NotificationPort] = None,
        number_repo: Any = None,  # PgWhatsAppNumberRepository
    ) -> None:
        self._agent_gateway = agent_gateway
        self._cache = cache
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._tenant_repo = tenant_repo
        self._notification = notification
        self._number_repo = number_repo

    async def execute(self, payload: dict[str, Any]) -> dict[str, str]:
        # Extract chat_id from gateway payload
        msg_payload = payload.get("payload", {})
        chat_id = msg_payload.get("from") or msg_payload.get("chatId", "")
        session = payload.get("session", "default")

        if not chat_id:
            logger.warning("gateway_proxy_no_chat_id", payload_keys=list(payload.keys()))
            await self._agent_gateway.forward_webhook(payload)
            return {"action": "forwarded", "reason": "no_chat_id"}

        # Check takeover state — value is "tenant_id:operator_id"
        takeover_key = f"{TAKEOVER_KEY_PREFIX}{session}:{chat_id}"
        takeover_value = await self._cache.get(takeover_key)

        if takeover_value:
            logger.info("gateway_proxy_takeover_active", chat_id=chat_id, session=session)
            # Parse tenant_id encoded in value (format: "tenant_id:operator_id")
            tenant_id_str = takeover_value.split(":")[0]
            try:
                tenant_id = UUID(tenant_id_str)
            except ValueError:
                # Legacy value format (just operator_id) — fall back to session lookup
                tenant_id = None
            await self._store_intercepted_message(chat_id, session, msg_payload, tenant_id)
            return {"action": "intercepted", "reason": "takeover_active"}

        # No takeover: forward to agents
        await self._agent_gateway.forward_webhook(payload)
        logger.debug("gateway_proxy_forwarded", chat_id=chat_id, session=session)
        return {"action": "forwarded", "reason": "no_takeover"}

    async def _store_intercepted_message(
        self,
        chat_id: str,
        session: str,
        msg_payload: dict,
        tenant_id: Optional[UUID] = None,
    ) -> None:
        """Store intercepted message so operator sees it in real-time."""
        if not (self._conversation_repo and self._message_repo and self._tenant_repo):
            return

        # Resolve tenant — prefer tenant_id from Redis, fall back to agent_id lookup
        tenant = None
        if tenant_id:
            tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            tenant = await self._tenant_repo.get_by_agent_id(session)
        if not tenant:
            logger.warning("tenant_not_found_for_takeover", session=session, chat_id=chat_id)
            return

        # Determine agent_id: prefer number-specific agent, fall back to tenant default
        active_agent_id = tenant.get_active_agent_id()
        if self._number_repo:
            number = await self._number_repo.get_by_session(session)
            if number and number.agent_id:
                active_agent_id = number.agent_id
        conversation = await self._conversation_repo.get_by_chat_id(tenant.id, chat_id, agent_id=active_agent_id)
        if not conversation:
            phone = chat_id.split("@")[0] if "@" in chat_id else chat_id
            conversation = Conversation.create(
                tenant_id=tenant.id,
                chat_id=chat_id,
                agent_id=active_agent_id,
                customer_phone=phone,
            )
            await self._conversation_repo.save(conversation)

        # Extract content from gateway payload
        content = (
            msg_payload.get("body")
            or msg_payload.get("text")
            or msg_payload.get("caption")
            or "[media]"
        )
        sender_name = msg_payload.get("pushName") or conversation.customer_name or ""

        message = CRMMessage.create(
            tenant_id=tenant.id,
            conversation_id=conversation.id,
            chat_id=chat_id,
            role="user",
            content=content,
            sender_name=sender_name,
        )
        await self._message_repo.save(message)

        now = datetime.utcnow()
        conversation.last_message_preview = content[:100]
        conversation.last_message_at = now
        conversation.unread_count += 1
        conversation.updated_at = now
        await self._conversation_repo.update(conversation)

        if self._notification:
            await self._notification.push_to_tenant(
                tenant.id,
                "new_message",
                {
                    "chat_id": chat_id,
                    "agent_id": active_agent_id,
                    "conversation_id": str(conversation.id),
                    "message": {
                        "id": str(message.id),
                        "role": message.role,
                        "content": message.content,
                        "sender_name": message.sender_name,
                        "created_at": message.created_at.isoformat(),
                    },
                },
            )
