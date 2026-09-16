from typing import Annotated

from fastapi import Depends

from src.db.database import SessionDep
from src.modules.users.repository import UserRepository
from src.modules.users.service import UserService


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(repo: UserRepositoryDep) -> UserService:
    return UserService(repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
