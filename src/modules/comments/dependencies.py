from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.comments.repository import CommentRepository
from src.modules.comments.service import CommentService
from src.modules.reviews.dependencies import ReviewServiceDep
from src.services.moderation_producer.dependencies import ModerationProducerDep


def get_comment_repository(session: SessionDep) -> CommentRepository:
    return CommentRepository(session)


CommentRepositoryDep = Annotated[CommentRepository, Depends(get_comment_repository)]


def get_comment_service(
    repo: CommentRepositoryDep,
    review_service: ReviewServiceDep,
    moderation_producer: ModerationProducerDep,
) -> CommentService:
    return CommentService(repo, review_service, moderation_producer)


CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
