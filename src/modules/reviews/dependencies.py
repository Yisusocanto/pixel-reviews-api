from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.games.dependencies import GameServiceDep
from src.modules.reviews.repository import ReviewRepository
from src.modules.reviews.service import ReviewService
from src.services.moderation_producer.dependencies import ModerationProducerDep


def get_review_repository(session: SessionDep) -> ReviewRepository:
    return ReviewRepository(session)


ReviewRepositoryDep = Annotated[ReviewRepository, Depends(get_review_repository)]


def get_review_service(
    repo: ReviewRepositoryDep,
    game_service: GameServiceDep,
    moderation_producer: ModerationProducerDep,
) -> ReviewService:
    return ReviewService(
        repo=repo, game_service=game_service, moderation_producer=moderation_producer
    )


ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
