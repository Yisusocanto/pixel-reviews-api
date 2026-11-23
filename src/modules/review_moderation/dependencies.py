from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.review_moderation.repository import ReviewModerationRepository
from src.modules.review_moderation.service import ReviewModerationService
from src.modules.reviews.dependencies import ReviewServiceDep


def get_review_moderation_repository(session: SessionDep) -> ReviewModerationRepository:
    """
    Dependency that provides an instance of ReviewModerationRepository.
    """
    return ReviewModerationRepository(session)


ReviewModerationRepositoryDep = Annotated[
    ReviewModerationRepository, Depends(get_review_moderation_repository)
]


def get_review_moderation_service(
    repo: ReviewModerationRepositoryDep, review_service: ReviewServiceDep
) -> ReviewModerationService:
    """
    Dependency that provides an instance of ReviewModerationService.
    """
    return ReviewModerationService(repo, review_service)


ReviewModerationServiceDep = Annotated[
    ReviewModerationService, Depends(get_review_moderation_service)
]
