from typing import Annotated

from fastapi import APIRouter, Query

from src.auth.dependencies import SessionDep
from src.users.models import UserResponse
from src.users.schema import UserPagination
from src.users.service import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserPagination)
async def get_all(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await user_service.get_all(session, page, limit)


@router.get("/{username}", response_model=UserResponse)
async def get_user(session: SessionDep, username: str):
    return await user_service.get_user(session, username)
