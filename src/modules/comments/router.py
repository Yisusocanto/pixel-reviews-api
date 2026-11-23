import uuid

from fastapi import APIRouter, BackgroundTasks

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.comments.dependencies import CommentServiceDep
from src.modules.comments.models import CommentCreate, CommentUpdate
from src.modules.comments.schemas import CommentResponse

router = APIRouter(
    prefix="/comments",
    tags=["Comments"],
)


@router.post("", response_model=CommentResponse)
async def create(
    service: CommentServiceDep,
    data: CommentCreate,
    user: CurrentUserDep,
    bg_tasks: BackgroundTasks,
):
    return await service.create(data, user.id, bg_tasks)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update(
    service: CommentServiceDep,
    comment_id: uuid.UUID,
    new_data: CommentUpdate,
    user: CurrentUserDep,
    bg_tasks: BackgroundTasks,
):
    return await service.update(comment_id, user.id, new_data, bg_tasks)


@router.post("/{comment_id}/appeal", response_model=CommentResponse)
async def appeal_comment(
    comment_id: uuid.UUID,
    service: CommentServiceDep,
    user: CurrentUserDep,
):
    return await service.appeal(comment_id=comment_id, user_id=user.id)


@router.delete("/{comment_id}", response_model=CommentResponse)
async def delete(service: CommentServiceDep, comment_id: uuid.UUID, user: CurrentUserDep):
    return await service.delete(comment_id, user.id)
