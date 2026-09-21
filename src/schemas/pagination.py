from typing import Any

from src.schemas.config_base import ConfigBase


class Pagination(ConfigBase):
    items: list[Any]
    page: int
    total: int
    total_pages: int
