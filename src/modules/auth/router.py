from fastapi import APIRouter, status

from src.modules.auth.dependencies import AuthServiceDep, CurrentUserDep
from src.modules.auth.models import AuthResponse, LoginRequest, RefreshTokenRequest, TokenResponse
from src.modules.users.models import User, UserCreate, UserResponse

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register and authenticate a new user",
)
async def register(
    user_data: UserCreate,
    service: AuthServiceDep,
) -> AuthResponse:
    return await service.register(user_data)


@auth_router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and obtain access & refresh tokens",
)
async def login(
    login_data: LoginRequest,
    service: AuthServiceDep,
) -> AuthResponse:
    return await service.login(login_data)


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
