from typing import Annotated

from fastapi import Depends

from src.db.database import SessionDep
from src.modules.developers.repository import DeveloperRepository
from src.modules.developers.service import DeveloperService


def get_developer_repository(session: SessionDep) -> DeveloperRepository:
    return DeveloperRepository(session)


DeveloperRepositoryDep = Annotated[DeveloperRepository, Depends(get_developer_repository)]


def get_developer_service(repo: DeveloperRepositoryDep) -> DeveloperService:
    return DeveloperService(repo)


DeveloperServiceDep = Annotated[DeveloperService, Depends(get_developer_service)]
