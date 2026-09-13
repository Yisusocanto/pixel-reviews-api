import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.security import TOKEN_TYPE_ACCESS, decode_token
from src.db.database import get_session
from src.users.models import User
from src.users.repository import user_repo

security_scheme = HTTPBearer(auto_error=True)
SessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)]


async def get_current_user(
    credentials: TokenDep,
    session: SessionDep,
) -> User:
    """
    Dependency that extracts the Bearer token from the request header,
    validates it as an access token, and fetches the associated user.
    """
    token = credentials.credentials
    payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)

    user_id_str = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError, TypeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
