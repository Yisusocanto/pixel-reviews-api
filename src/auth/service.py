import uuid

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.models import AuthResponse, LoginRequest, TokenResponse
from src.auth.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.lib.password_handler import check_password
from src.users.models import User, UserCreate, UserResponse
from src.users.repository import user_repo
from src.users.service import user_service


class AuthService:
    async def register(self, session: AsyncSession, data: UserCreate) -> AuthResponse:
        """Registers a new user and immediately authenticates them with access and refresh tokens."""
        user = await user_service.create(session, data)

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
        session: AsyncSession,
        email: str,
        password: str,
    ) -> User:
        """Verifies credentials and returns user if valid."""
        user = await user_repo.get_by_email(session, email)
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

    async def login(self, session: AsyncSession, data: LoginRequest) -> AuthResponse:
        """Authenticates user and issues access and refresh tokens along with user info."""
        user = await self.authenticate_user(session, data.email, data.password)

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
        session: AsyncSession,
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

        user = await user_repo.get_user(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Refresh token rotation: issue both new access token and new refresh token
        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )


auth_service = AuthService()
