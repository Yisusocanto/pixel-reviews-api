from typing import Annotated

from fastapi import Depends

from src.db.database import SessionDep
from src.modules.publisher.repository import PublisherRepository
from src.modules.publisher.service import PublisherService


def get_publisher_repository(session: SessionDep) -> PublisherRepository:
    return PublisherRepository(session)


PublisherRepositoryDep = Annotated[PublisherRepository, Depends(get_publisher_repository)]


def get_publisher_service(repo: PublisherRepositoryDep) -> PublisherService:
    return PublisherService(repo)


PublisherServiceDep = Annotated[PublisherService, Depends(get_publisher_service)]
