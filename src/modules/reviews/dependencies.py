from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.reviews.repository import ReviewRepository
from src.modules.reviews.service import ReviewService


def get_review_repository(session: SessionDep) -> ReviewRepository:
    return ReviewRepository(session)


ReviewRepositoryDep = Annotated[ReviewRepository, Depends(get_review_repository)]


def get_review_service(repo: ReviewRepositoryDep) -> ReviewService:
    return ReviewService(repo)


ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
