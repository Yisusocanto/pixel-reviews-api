import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status

from src.core.settings import settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_token(subject: uuid.UUID | str, token_type: str, expires_delta: timedelta) -> str:
    """Creates an encoded JWT token with subject, type, issue time, and expiration."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "exp": now + expires_delta,
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID | str) -> str:
    """Generates a short-lived access token."""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(subject=user_id, token_type=TOKEN_TYPE_ACCESS, expires_delta=expires)


def create_refresh_token(user_id: uuid.UUID | str) -> str:
    """Generates a long-lived refresh token."""
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(subject=user_id, token_type=TOKEN_TYPE_REFRESH, expires_delta=expires)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """
    Decodes and validates a JWT token.
    Checks signature, expiration, subject existence, and token type.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected '{expected_type}' token, received '{token_type}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload.get("sub"):
        raise credentials_exception

    return payload
