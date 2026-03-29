from dataclasses import dataclass
from uuid import UUID

from core.domain.conversation import CRMMessage
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.message_repository import MessageRepositoryPort


@dataclass(frozen=True)
class GetMessagesResult:
    items: list[CRMMessage]
    total: int
    offset: int
    limit: int


class GetConversationMessagesUseCase:

    def __init__(
        self,
        conversation_repo: ConversationRepositoryPort,
        message_repo: MessageRepositoryPort,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo

    async def execute(
        self, tenant_id: UUID, chat_id: str,
        offset: int = 0, limit: int = 100, order: str = "asc",
        agent_id: str | None = None,
    ) -> GetMessagesResult:
        conversation = await self._conversation_repo.get_by_chat_id(tenant_id, chat_id, agent_id=agent_id)
        if not conversation:
            raise ValueError("Conversation not found")

        items, total = await self._message_repo.list_by_conversation(
            tenant_id, conversation.id, offset, limit, order=order,
        )
        return GetMessagesResult(items=items, total=total, offset=offset, limit=limit)
