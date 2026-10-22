from fastapi import APIRouter, Request, status

from src.lib.limiter import limiter
from src.modules.auth.dependencies import AuthServiceDep, CurrentUserDep
from src.modules.auth.models import (
    AuthResponse,
    GoogleLoginRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from src.modules.users.models import User, UserCreate, UserResponse

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register and authenticate a new user",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    service: AuthServiceDep,
) -> AuthResponse:
    return await service.register(user_data)


@auth_router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and obtain access & refresh tokens",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    service: AuthServiceDep,
) -> AuthResponse:
    return await service.login(login_data)


@auth_router.post(
    "/google",
    response_model=AuthResponse,
    summary="Authenticate with Google ID token",
)
@limiter.limit("10/minute")
async def google_login(
    request: Request,
    data: GoogleLoginRequest,
    service: AuthServiceDep,
) -> AuthResponse:
    return await service.login_with_google(data.id_token)


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using a refresh token",
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.refresh_tokens(refresh_data.refresh_token)


@auth_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: CurrentUserDep,
) -> User:
    return current_user
