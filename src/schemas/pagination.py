from typing import Any

from pydantic import BaseModel


class Pagination(BaseModel):
    items: list[Any]
    page: int
    total: int
    total_pages: int
