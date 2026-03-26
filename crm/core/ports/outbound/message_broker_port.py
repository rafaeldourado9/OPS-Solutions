from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


@dataclass
class CRMEvent:
    event_type: str          # e.g. "crm.lead.stage_changed"
    tenant_id: str
    payload: dict[str, Any]
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def routing_key(self) -> str:
        return self.event_type


class MessageBrokerPort(ABC):

    @abstractmethod
    async def publish(self, event: CRMEvent) -> None:
        """Publish a domain event to the broker. Fire-and-forget."""
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
