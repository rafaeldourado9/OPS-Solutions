import io
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from core.ports.outbound.storage_port import StoragePort
from infrastructure.config import settings


class MinioStorageAdapter(StoragePort):

    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_url,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    async def download(self, key: str) -> bytes:
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error:
            pass  # Object may not exist

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        return self._client.presigned_get_object(
            self._bucket,
            key,
            expires=timedelta(seconds=expires_in),
        )
