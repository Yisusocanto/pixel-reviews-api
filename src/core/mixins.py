from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """
    Mixin that provides automated created_at and updated_at timestamps.
    - created_at: populated automatically upon creation (both Python-side and DB-side).
    - updated_at: populated automatically upon creation and automatically updated
                  on every SQL UPDATE statement via SQLAlchemy's onupdate hook.
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
            "nullable": False,
        },
    )
