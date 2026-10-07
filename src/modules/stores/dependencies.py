from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.stores.repository import StoreRepository
from src.modules.stores.service import StoreService


def get_store_repository(session: SessionDep) -> StoreRepository:
    return StoreRepository(session)


StoreRepositoryDep = Annotated[StoreRepository, Depends(get_store_repository)]


def get_store_service(repo: StoreRepositoryDep) -> StoreService:
    return StoreService(repo)


StoreServiceDep = Annotated[StoreService, Depends(get_store_service)]
