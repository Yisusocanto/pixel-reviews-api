from pydantic import BaseModel, EmailStr

from src.users.models import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str
