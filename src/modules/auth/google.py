from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from src.core.settings import settings

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")

_jwks_client = PyJWKClient(GOOGLE_JWKS_URL, cache_keys=True)


def verify_google_id_token(token: str) -> dict[str, Any]:
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None,
            options={
                "require": ["exp", "iss", "aud", "sub"],
                "verify_aud": bool(settings.GOOGLE_CLIENT_ID),
            },
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("iss") not in GOOGLE_ISSUERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token issuer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
