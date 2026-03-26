from abc import ABC, abstractmethod
from typing import Any


class AgentGatewayPort(ABC):

    @abstractmethod
    async def get_health(self) -> dict[str, Any]: ...

    @abstractmethod
    async def forward_webhook(self, payload: dict[str, Any]) -> None:
        """Forward raw gateway webhook payload to agents API."""
        ...
