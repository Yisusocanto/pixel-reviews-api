import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.reviews.dependencies import ReviewServiceDep
from src.modules.reviews.models import ReviewCreate
from src.modules.reviews.schemas import ReviewPagination, ReviewResponse

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.get("", response_model=ReviewPagination)
async def get_all(
    service: ReviewServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_all(page, limit)


@router.post("", response_model=ReviewResponse)
async def create(
    data: ReviewCreate,
    service: ReviewServiceDep,
    current_user: CurrentUserDep,
):
    return await service.create(data, current_user.id)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_by_id(review_id: uuid.UUID, service: ReviewServiceDep):
    return await service.get_by_id(review_id)
