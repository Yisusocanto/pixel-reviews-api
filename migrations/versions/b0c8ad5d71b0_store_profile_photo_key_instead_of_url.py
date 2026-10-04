"""store profile photo key instead of url

Revision ID: b0c8ad5d71b0
Revises: 561b0bd82b56
Create Date: 2026-10-04 13:47:25.166877

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b0c8ad5d71b0"
down_revision: str | Sequence[str] | None = "561b0bd82b56"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("users_profile_photo_url_key", "users", type_="unique")
    op.alter_column("users", "profile_photo_url", new_column_name="profile_photo_key")
    op.execute("UPDATE users SET profile_photo_key = NULL")


def downgrade() -> None:
    op.execute("UPDATE users SET profile_photo_key = NULL")
    op.alter_column("users", "profile_photo_key", new_column_name="profile_photo_url")
    op.create_unique_constraint("users_profile_photo_url_key", "users", ["profile_photo_url"])
