"""add google_id and make hashed_password nullable

Revision ID: 51bdd4a7436f
Revises: 33953384d46d
Create Date: 2026-10-13 13:00:22.418053

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "51bdd4a7436f"
down_revision: str | Sequence[str] | None = "33953384d46d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_id", sa.String(), nullable=True))
    op.alter_column("users", "hashed_password", existing_type=sa.VARCHAR(), nullable=True)
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.alter_column("users", "hashed_password", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("users", "google_id")
