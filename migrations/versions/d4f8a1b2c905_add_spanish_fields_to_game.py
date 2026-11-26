"""add_spanish_fields_to_game

Revision ID: d4f8a1b2c905
Revises: c3a9d4e7f120
Create Date: 2026-11-25 23:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4f8a1b2c905"
down_revision: str | Sequence[str] | None = "c3a9d4e7f120"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("game", sa.Column("description_es", sa.String(), nullable=True))
    op.add_column("game", sa.Column("storyline_es", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("game", "storyline_es")
    op.drop_column("game", "description_es")
