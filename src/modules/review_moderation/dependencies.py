import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from src.core.settings import settings
from src.modules.auth.dependencies import SessionDep
from src.modules.review_moderation.repository import ReviewModerationRepository
from src.modules.review_moderation.service import ReviewModerationService
from src.modules.reviews.dependencies import ReviewServiceDep


def verify_service_key(x_service_key: Annotated[str | None, Header()]):
    """
    Dependency that verifies the presence and validity of the X-Service-Key header.
    Raises an HTTPException if the key is missing or invalid.
    """
    if not hmac.compare_digest(x_service_key or "", settings.MODERATION_SERVICE_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing service key",
        )


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
