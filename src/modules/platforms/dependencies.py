from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.platforms.repository import PlatformRepository
from src.modules.platforms.service import PlatformService


def get_platform_repository(session: SessionDep) -> PlatformRepository:
    return PlatformRepository(session)


PlatformRepositoryDep = Annotated[PlatformRepository, Depends(get_platform_repository)]


def get_platform_service(repo: PlatformRepositoryDep) -> PlatformService:
    return PlatformService(repo)


PlatformServiceDep = Annotated[PlatformService, Depends(get_platform_service)]
