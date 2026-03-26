from abc import ABC, abstractmethod


class StoragePort(ABC):

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None: ...

    @abstractmethod
    async def download(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str: ...
