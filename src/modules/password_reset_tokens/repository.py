import uuid

from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.password_reset_tokens.models import PasswordResetToken, PasswordResetTokenCreate


class PasswordResetTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: PasswordResetTokenCreate) -> PasswordResetToken:
        new_token = PasswordResetToken(**data.model_dump())
        self.session.add(new_token)
        await self.session.flush()
        await self.session.refresh(new_token)
        return new_token

    async def delete_all(self, user_id: uuid.UUID):
        stmt = delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.rowcount

    async def get_one(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        result = await self.session.exec(stmt)
        return result.first()
