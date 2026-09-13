from src.schemas.pagination import Pagination
from src.users.models import UserResponse


class UserPagination(Pagination):
    items: list[UserResponse]
