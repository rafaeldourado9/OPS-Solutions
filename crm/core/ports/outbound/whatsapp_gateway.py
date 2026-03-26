from abc import ABC, abstractmethod


class WhatsAppGatewayPort(ABC):

    @abstractmethod
    async def send_message(self, session: str, chat_id: str, text: str) -> None: ...

    @abstractmethod
    async def send_typing(self, session: str, chat_id: str, active: bool) -> None: ...

    @abstractmethod
    async def send_document(
        self, session: str, chat_id: str, doc_data: bytes, filename: str, caption: str = ""
    ) -> None: ...

    @abstractmethod
    async def send_seen(self, session: str, chat_id: str) -> None: ...
