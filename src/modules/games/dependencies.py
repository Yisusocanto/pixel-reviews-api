from typing import Annotated

from fastapi import Depends

from src.db.database import SessionDep
from src.modules.developers.dependencies import DeveloperServiceDep
from src.modules.games.repository import GameRepository
from src.modules.games.service import GameService
from src.modules.publisher.dependencies import PublisherServiceDep
from src.modules.reviews.dependencies import ReviewServiceDep


def get_game_repository(session: SessionDep) -> GameRepository:
    return GameRepository(session)


GameRepositoryDep = Annotated[GameRepository, Depends(get_game_repository)]


def get_game_service(
    repo: GameRepositoryDep,
    dev_service: DeveloperServiceDep,
    pub_service: PublisherServiceDep,
    review_service: ReviewServiceDep,
) -> GameService:
    return GameService(
        repo=repo, dev_service=dev_service, pub_service=pub_service, review_service=review_service
    )


GameServiceDep = Annotated[GameService, Depends(get_game_service)]
