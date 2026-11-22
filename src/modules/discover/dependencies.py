from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.discover.repository import DiscoverRepository
from src.modules.discover.service import DiscoverService


def get_discover_repository(session: SessionDep) -> DiscoverRepository:
    return DiscoverRepository(session)


DiscoverRepositoryDep = Annotated[DiscoverRepository, Depends(get_discover_repository)]


def get_discover_service(repo: DiscoverRepositoryDep) -> DiscoverService:
    return DiscoverService(repo)


DiscoverServiceDep = Annotated[DiscoverService, Depends(get_discover_service)]
