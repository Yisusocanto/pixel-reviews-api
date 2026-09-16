import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.db.database import SessionDep
from src.modules.auth.security import TOKEN_TYPE_ACCESS, decode_token
from src.modules.auth.service import AuthService
from src.modules.users.dependencies import UserRepositoryDep, UserServiceDep
from src.modules.users.models import User

security_scheme = HTTPBearer(auto_error=True)
TokenDep = Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)]


async def get_current_user(
    credentials: TokenDep,
    user_repo: UserRepositoryDep,
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

    user = await user_repo.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_auth_service(
    user_repo: UserRepositoryDep,
    user_service: UserServiceDep,
) -> AuthService:
    return AuthService(user_repo=user_repo, user_service=user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

__all__ = ["AuthServiceDep", "CurrentUserDep", "SessionDep", "TokenDep"]
