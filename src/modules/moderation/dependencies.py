import hmac
from typing import Annotated

from fastapi import Header, HTTPException, status

from src.core.settings import settings


def verify_service_key(x_service_key: Annotated[str | None, Header()]) -> None:
    """
    Dependency that verifies the presence and validity of the X-Service-Key header.
    Raises an HTTPException if the key is missing or invalid.
    """
    if not hmac.compare_digest(x_service_key or "", settings.MODERATION_SERVICE_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing service key",
        )
