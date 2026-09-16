from src.modules.users.models import UserResponse
from src.schemas.pagination import Pagination


class UserPagination(Pagination):
    items: list[UserResponse]
