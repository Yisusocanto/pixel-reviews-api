from typing import Annotated

from fastapi import Depends

from src.db.database import SessionDep
from src.modules.social_studio.repository import SocialStudioRepository
from src.modules.social_studio.service import SocialStudioService
from src.services.gemini.dependencies import GeminiServiceDep
from src.services.storage.dependencies import StorageServiceDep


def get_social_studio_repo(session: SessionDep) -> SocialStudioRepository:
    return SocialStudioRepository(session=session)


SocialStudioRepoDep = Annotated[SocialStudioRepository, Depends(get_social_studio_repo)]


def get_social_studio_service(
    repo: SocialStudioRepoDep,
    gemini: GeminiServiceDep,
    storage: StorageServiceDep,
) -> SocialStudioService:
    return SocialStudioService(repo=repo, gemini=gemini, storage=storage)


SocialStudioServiceDep = Annotated[SocialStudioService, Depends(get_social_studio_service)]
