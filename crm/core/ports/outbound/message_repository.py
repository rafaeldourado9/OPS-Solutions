from abc import ABC, abstractmethod
from uuid import UUID

from core.domain.conversation import CRMMessage


class MessageRepositoryPort(ABC):

    @abstractmethod
    async def save(self, message: CRMMessage) -> None: ...

    @abstractmethod
    async def list_by_conversation(
        self, tenant_id: UUID, conversation_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[CRMMessage], int]: ...
