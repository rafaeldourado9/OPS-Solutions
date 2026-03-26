import base64

import httpx
import structlog

from core.ports.outbound.whatsapp_gateway import WhatsAppGatewayPort
from infrastructure.config import settings

logger = structlog.get_logger()


class WhatsAppDirectGateway(WhatsAppGatewayPort):
    """Direct gateway REST calls for operator messages during human takeover."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._base_url = (base_url or settings.gateway_url).rstrip("/")
        self._api_key = api_key or settings.gateway_api_key
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        self._client = httpx.AsyncClient(timeout=10.0, headers=headers)

    async def send_message(self, session: str, chat_id: str, text: str) -> None:
        await self._client.post(
            f"{self._base_url}/api/sendText",
            json={"session": session, "chatId": chat_id, "text": text},
        )

    async def send_typing(self, session: str, chat_id: str, active: bool) -> None:
        endpoint = "startTyping" if active else "stopTyping"
        try:
            await self._client.post(
                f"{self._base_url}/api/{endpoint}",
                json={"session": session, "chatId": chat_id},
            )
        except httpx.HTTPError:
            pass  # typing is best-effort

    async def send_document(
        self, session: str, chat_id: str, doc_data: bytes, filename: str, caption: str = ""
    ) -> None:
        b64 = base64.b64encode(doc_data).decode("utf-8")
        await self._client.post(
            f"{self._base_url}/api/sendFile",
            json={
                "session": session,
                "chatId": chat_id,
                "file": {"data": b64, "filename": filename},
                "caption": caption,
            },
        )

    async def send_seen(self, session: str, chat_id: str) -> None:
        try:
            await self._client.post(
                f"{self._base_url}/api/sendSeen",
                json={"session": session, "chatId": chat_id},
            )
        except httpx.HTTPError:
            pass

    async def close(self) -> None:
        await self._client.aclose()
