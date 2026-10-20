from typing import Annotated

from fastapi.params import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.password_reset_tokens.repository import PasswordResetTokenRepository
from src.modules.password_reset_tokens.service import PasswordResetTokenService


def get_password_reset_token_repo(session: SessionDep) -> PasswordResetTokenRepository:
    return PasswordResetTokenRepository(session)


PasswordResetTokenRepositoryDep = Annotated[
    PasswordResetTokenRepository, Depends(get_password_reset_token_repo)
]


def get_password_reset_token_service(
    repo: PasswordResetTokenRepositoryDep,
) -> PasswordResetTokenService:
    return PasswordResetTokenService(repo)


PasswordResetTokenServiceDep = Annotated[
    PasswordResetTokenService, Depends(get_password_reset_token_repo)
]
