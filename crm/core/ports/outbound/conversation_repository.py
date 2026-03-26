from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from core.domain.conversation import Conversation


class ConversationRepositoryPort(ABC):

    @abstractmethod
    async def save(self, conversation: Conversation) -> None: ...

    @abstractmethod
    async def update(self, conversation: Conversation) -> None: ...

    @abstractmethod
    async def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[Conversation]: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, conversation_id: UUID) -> Optional[Conversation]: ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[Conversation], int]: ...
