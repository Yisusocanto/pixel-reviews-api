from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.likes.repository import LikeRepository
from src.modules.likes.service import LikeService
from src.modules.reviews.dependencies import ReviewServiceDep


def get_like_repository(session: SessionDep) -> LikeRepository:
    return LikeRepository(session)


LikeRepositoryDep = Annotated[LikeRepository, Depends(get_like_repository)]


def get_like_service(
    repo: LikeRepositoryDep,
    review_service: ReviewServiceDep,
) -> LikeService:
    return LikeService(repo=repo, review_service=review_service)


LikeServiceDep = Annotated[LikeService, Depends(get_like_service)]
