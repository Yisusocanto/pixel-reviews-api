import json

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def get_email_key(request: Request) -> str:
    try:
        body = json.loads(request._body)
        if not isinstance(body, dict):
            return get_remote_address(request)
        email = body.get("email")
        if not isinstance(email, str):
            return get_remote_address(request)
        return email.strip().lower() or get_remote_address(request)
    except AttributeError, UnicodeDecodeError, json.JSONDecodeError, TypeError:
        return get_remote_address(request)
