from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.comment_moderation.repository import CommentModerationRepository
from src.modules.comment_moderation.service import CommentModerationService
from src.modules.comments.dependencies import CommentServiceDep


def get_comment_moderation_repo(session: SessionDep) -> CommentModerationRepository:
    return CommentModerationRepository(session)


CommentModerationRepositoryDep = Annotated[
    CommentModerationRepository, Depends(get_comment_moderation_repo)
]


def get_comment_moderation_service(
    repo: CommentModerationRepositoryDep, comment_service: CommentServiceDep
) -> CommentModerationService:
    return CommentModerationService(repo=repo, comment_service=comment_service)


CommentModerationServiceDep = Annotated[
    CommentModerationService, Depends(get_comment_moderation_service)
]
