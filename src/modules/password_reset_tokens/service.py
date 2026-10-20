import uuid

from src.modules.password_reset_tokens.models import PasswordResetToken, PasswordResetTokenCreate
from src.modules.password_reset_tokens.repository import PasswordResetTokenRepository


class PasswordResetTokenService:
    def __init__(self, repo: PasswordResetTokenRepository):
        self.repo = repo

    async def create(self, data: PasswordResetTokenCreate) -> PasswordResetToken:
        return await self.repo.create(data)

    async def delete_all(self, user_id: uuid.UUID):
        return await self.repo.delete_all(user_id)

    async def get_one(self, token_hash: str) -> PasswordResetToken | None:
        return await self.repo.get_one(token_hash)
