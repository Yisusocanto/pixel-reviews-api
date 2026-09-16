import uuid

from fastapi import HTTPException, status

from src.lib.password_handler import check_password
from src.modules.auth.models import AuthResponse, LoginRequest, TokenResponse
from src.modules.auth.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.modules.users.models import User, UserCreate, UserResponse
from src.modules.users.repository import UserRepository
from src.modules.users.service import UserService


class AuthService:
    def __init__(self, user_repo: UserRepository, user_service: UserService) -> None:
        self.user_repo = user_repo
        self.user_service = user_service

    async def register(self, data: UserCreate) -> AuthResponse:
        """Registers a new user and immediately authenticates them with access and refresh tokens."""
        user = await self.user_service.create(data)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:
        """Verifies credentials and returns user if valid."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        is_valid = await check_password(password, user.hashed_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    async def login(self, data: LoginRequest) -> AuthResponse:
        """Authenticates user and issues access and refresh tokens along with user info."""
        user = await self.authenticate_user(data.email, data.password)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Validates refresh token and issues a new pair of tokens (Refresh Token Rotation).
        """
        payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
        user_id_str = payload.get("sub")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError, TypeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self.user_repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
