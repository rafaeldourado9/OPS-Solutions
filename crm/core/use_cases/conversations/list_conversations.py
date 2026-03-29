from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.domain.conversation import Conversation
from core.ports.outbound.conversation_repository import ConversationRepositoryPort


@dataclass(frozen=True)
class ListConversationsResult:
    items: list[Conversation]
    total: int
    offset: int
    limit: int


class ListConversationsUseCase:

    def __init__(self, conversation_repo: ConversationRepositoryPort) -> None:
        self._repo = conversation_repo

    async def execute(
        self, tenant_id: UUID, status: Optional[str] = None, offset: int = 0, limit: int = 50,
        agent_id: Optional[str] = None,
    ) -> ListConversationsResult:
        items, total = await self._repo.list_by_tenant(tenant_id, status, offset, limit, agent_id=agent_id)
        return ListConversationsResult(items=items, total=total, offset=offset, limit=limit)
