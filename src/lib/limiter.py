import json

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def get_email_key(request: Request) -> str:
    try:
        body = json.loads(request._body)
        return body.get("email", "").strip().lower() or get_remote_address(request)
    except Exception:
        return get_remote_address(request)
