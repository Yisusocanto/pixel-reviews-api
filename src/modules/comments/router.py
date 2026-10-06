import uuid

from fastapi import APIRouter

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.comments.dependencies import CommentServiceDep
from src.modules.comments.models import CommentCreate, CommentUpdate
from src.modules.comments.schemas import CommentResponse

router = APIRouter(
    prefix="/comments",
    tags=["Comments"],
)


@router.post("", response_model=CommentResponse)
async def create(service: CommentServiceDep, data: CommentCreate, user: CurrentUserDep):
    return await service.create(data, user.id)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update(
    service: CommentServiceDep, comment_id: uuid.UUID, new_data: CommentUpdate, user: CurrentUserDep
):
    return await service.update(comment_id, user.id, new_data)


@router.delete("/{comment_id}", response_model=CommentResponse)
async def delete(service: CommentServiceDep, comment_id: uuid.UUID, user: CurrentUserDep):
    return await service.delete(comment_id, user.id)
