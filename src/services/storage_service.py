import asyncio
import logging

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("storage_service")


class StorageError(Exception):
    pass


class StorageService:
    def __init__(self, client: BaseClient, bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        cache_control: str | None = None,
    ) -> None:
        extra_args = {"CacheControl": cache_control} if cache_control else {}
        try:
            await asyncio.to_thread(
                self.client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                **extra_args,
            )
        except (ClientError, BotoCoreError) as error:
            logger.exception("[STORAGE] Failed to upload %s", key)
            raise StorageError(f"Could not upload {key}") from error

        logger.info("[STORAGE] Uploaded %s (%d bytes, %s)", key, len(data), content_type)

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)
        except (ClientError, BotoCoreError) as error:
            logger.exception("[STORAGE] Failed to delete %s", key)
            raise StorageError(f"Could not delete {key}") from error

        logger.info("[STORAGE] Deleted %s", key)
