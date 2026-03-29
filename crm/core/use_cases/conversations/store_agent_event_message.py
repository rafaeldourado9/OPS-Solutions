from datetime import datetime
from typing import Optional
from uuid import UUID

import re

import structlog

from core.domain.conversation import CRMMessage, Conversation


def _strip_internal_context(text: str) -> str:
    """Remove internal LLM context annotations injected by the agent's media processor.

    Examples stripped:
      "transcrição\n[contexto: mensagem de voz — responda ao conteúdo acima como se fosse texto normal]"
      → "transcrição"
    """
    # Strip trailing [contexto: ...] block (any variant)
    text = re.sub(r'\n\[contexto:[^\]]*\]$', '', text.strip(), flags=re.IGNORECASE)
    return text.strip()
from core.domain.events import InboundAgentEvent
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.customer_repository import CustomerRepositoryPort
from core.ports.outbound.message_repository import MessageRepositoryPort
from core.ports.outbound.notification_port import NotificationPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort

logger = structlog.get_logger()


class StoreAgentEventMessageUseCase:
    """
    Stores messages from agent events (message_received, agent_response_sent)
    into CRM's own conversation log and pushes real-time via WebSocket.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepositoryPort,
        message_repo: MessageRepositoryPort,
        customer_repo: CustomerRepositoryPort,
        tenant_repo: TenantRepositoryPort,
        notification: NotificationPort,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._customer_repo = customer_repo
        self._tenant_repo = tenant_repo
        self._notification = notification

    async def execute(self, event: InboundAgentEvent) -> Optional[CRMMessage]:
        if event.event_type not in ("message_received", "agent_response_sent"):
            return None

        tenant = await self._tenant_repo.get_by_agent_id(event.agent_id)
        if not tenant:
            # Fallback: check settings.owned_agents JSON for any tenant that owns this agent
            tenant = await self._tenant_repo.get_by_owned_agent_id(event.agent_id)
        if not tenant:
            logger.warning("tenant_not_found_for_agent", agent_id=event.agent_id)
            return None

        # Get or create conversation — scoped to this specific agent
        push_name_early = event.data.get("push_name", "")
        conversation = await self._conversation_repo.get_by_chat_id(tenant.id, event.chat_id, agent_id=event.agent_id)
        if not conversation:
            phone = event.chat_id.split("@")[0] if "@" in event.chat_id else event.chat_id
            customer = await self._customer_repo.get_by_phone(tenant.id, phone)
            display_name = push_name_early or (customer.name if customer else None) or phone
            conversation = Conversation.create(
                tenant_id=tenant.id,
                chat_id=event.chat_id,
                agent_id=event.agent_id,
                customer_phone=phone,
                customer_name=display_name,
                customer_id=customer.id if customer else None,
            )
            await self._conversation_repo.save(conversation)
        elif push_name_early and (not conversation.customer_name or conversation.customer_name == conversation.customer_phone):
            # Update name if it was previously set to the raw phone number
            conversation.customer_name = push_name_early
            await self._conversation_repo.update(conversation)

        # Determine role and content
        if event.event_type == "message_received":
            role = "user"
            # Agent sends data={"messages": ["msg1", "msg2"], "count": N, "push_name": "..."}
            messages = event.data.get("messages")
            if isinstance(messages, list) and messages:
                content = "\n".join(_strip_internal_context(str(m)) for m in messages)
            else:
                content = _strip_internal_context(event.data.get("content", event.data.get("body", "")))
            push_name = event.data.get("push_name", "")
            sender_name = push_name or conversation.customer_name
        else:
            role = "agent"
            content = event.data.get("content", event.data.get("response", ""))
            sender_name = event.data.get("agent_name", event.agent_id)

        if not content:
            return None

        # Save message
        message = CRMMessage.create(
            tenant_id=tenant.id,
            conversation_id=conversation.id,
            chat_id=event.chat_id,
            role=role,
            content=content,
            sender_name=sender_name,
        )
        await self._message_repo.save(message)

        # Update conversation preview
        now = datetime.utcnow()
        conversation.last_message_preview = content[:100]
        conversation.last_message_at = now
        conversation.updated_at = now
        if role == "user":
            conversation.unread_count += 1
        await self._conversation_repo.update(conversation)

        # Push real-time to WebSocket
        await self._notification.push_to_tenant(
            tenant.id,
            "new_message",
            {
                "chat_id": event.chat_id,
                "agent_id": event.agent_id,
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

        return message
