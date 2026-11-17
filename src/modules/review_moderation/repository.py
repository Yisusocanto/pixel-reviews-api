from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.review_moderation.models import ReviewModeration


class ReviewModerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ReviewModeration) -> ReviewModeration:
        self.session.add(data)
        await self.session.flush()
        await self.session.refresh(data)
        return data
