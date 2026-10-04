from functools import lru_cache
from typing import Annotated

import boto3
from botocore.client import BaseClient
from fastapi import Depends

from src.core.settings import settings
from src.services.storage_service import StorageService


@lru_cache
def get_storage_client() -> BaseClient:
    return boto3.client(
        service_name="s3",
        endpoint_url=f"https://{settings.CF_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.CF_ACCESS_KEY_ID,
        aws_secret_access_key=settings.CF_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def get_storage_service() -> StorageService:
    return StorageService(client=get_storage_client(), bucket=settings.CF_BUCKET)


StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]
