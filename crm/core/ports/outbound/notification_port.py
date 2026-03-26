from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class NotificationPort(ABC):

    @abstractmethod
    async def push_to_tenant(self, tenant_id: UUID, event_type: str, data: dict[str, Any]) -> None:
        """Push real-time event to all connected WebSocket clients of a tenant."""
        ...
