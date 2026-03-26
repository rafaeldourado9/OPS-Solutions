from typing import Any

import httpx
import structlog

from core.ports.outbound.agent_gateway import AgentGatewayPort
from infrastructure.config import settings

logger = structlog.get_logger()


class AgentAPIGateway(AgentGatewayPort):
    """HTTP client that talks to the agents FastAPI app."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.agents_api_url).rstrip("/")
        self._client = httpx.AsyncClient(timeout=10.0)

    async def get_health(self) -> dict[str, Any]:
        resp = await self._client.get(f"{self._base_url}/health")
        resp.raise_for_status()
        return resp.json()

    async def forward_webhook(self, payload: dict[str, Any]) -> None:
        try:
            resp = await self._client.post(
                f"{self._base_url}/webhook",
                json=payload,
                timeout=5.0,
            )
            if resp.status_code >= 400:
                logger.warning(
                    "agent_webhook_forward_failed",
                    status=resp.status_code,
                    body=resp.text[:200],
                )
        except httpx.HTTPError as e:
            logger.error("agent_webhook_forward_error", error=str(e))

    async def close(self) -> None:
        await self._client.aclose()
