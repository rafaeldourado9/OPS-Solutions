from datetime import datetime
from uuid import UUID

import structlog

from core.domain.conversation import CRMMessage
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.message_repository import MessageRepositoryPort
from core.ports.outbound.notification_port import NotificationPort
from core.ports.outbound.whatsapp_gateway import WhatsAppGatewayPort

logger = structlog.get_logger()


class SendOperatorMessageUseCase:
    """Operator sends a message to the customer via WhatsApp gateway during takeover."""

    def __init__(
        self,
        conversation_repo: ConversationRepositoryPort,
        message_repo: MessageRepositoryPort,
        whatsapp_gateway: WhatsAppGatewayPort,
        notification: NotificationPort,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._whatsapp_gateway = whatsapp_gateway
        self._notification = notification

    async def execute(
        self,
        tenant_id: UUID,
        chat_id: str,
        operator_id: UUID,
        operator_name: str,
        content: str,
        gateway_session: str = "default",
    ) -> CRMMessage:
        conversation = await self._conversation_repo.get_by_chat_id(tenant_id, chat_id)
        if not conversation:
            raise ValueError("Conversation not found")

        if not conversation.is_takeover_active:
            raise ValueError("Takeover not active — cannot send operator message")

        # Send via gateway directly to WhatsApp
        await self._whatsapp_gateway.send_message(gateway_session, chat_id, content)

        # Store message in CRM
        message = CRMMessage.create(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            chat_id=chat_id,
            role="operator",
            content=content,
            sender_name=operator_name,
        )
        await self._message_repo.save(message)

        # Update conversation preview
        now = datetime.utcnow()
        conversation.last_message_preview = content[:100]
        conversation.last_message_at = now
        conversation.updated_at = now
        await self._conversation_repo.update(conversation)

        # Push WebSocket event
        await self._notification.push_to_tenant(
            tenant_id,
            "new_message",
            {
                "chat_id": chat_id,
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

        logger.info("operator_message_sent", chat_id=chat_id, operator_id=str(operator_id))
        return message
