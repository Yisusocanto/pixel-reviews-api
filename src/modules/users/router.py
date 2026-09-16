from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.users.dependencies import UserServiceDep
from src.modules.users.models import UserResponse
from src.modules.users.schema import UserPagination

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserPagination)
async def get_all(
    service: UserServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_all(page, limit)


@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str, service: UserServiceDep):
    return await service.get_user(username)
