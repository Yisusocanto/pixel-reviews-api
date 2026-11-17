"""add_roles_and_review_moderation

Revision ID: 6a61f0f23946
Revises: 45ab207c96af
Create Date: 2026-11-15 14:47:12.254162

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "6a61f0f23946"
down_revision: str | Sequence[str] | None = "45ab207c96af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "review_moderation",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("content_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("verdict", sa.String(), nullable=False),
        sa.Column("judge", sa.String(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("scores", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=True),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["review_id"], ["review.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_moderation_review_id"), "review_moderation", ["review_id"], unique=False
    )

    op.add_column(
        "review",
        sa.Column("moderation_status", sa.String(), server_default="pending", nullable=False),
    )
    op.add_column(
        "review", sa.Column("moderation_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )
    op.add_column(
        "review", sa.Column("content_version", sa.Integer(), server_default="1", nullable=False)
    )
    op.add_column(
        "review", sa.Column("moderated_version", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "review", sa.Column("moderation_enqueued_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        op.f("ix_review_moderation_status"), "review", ["moderation_status"], unique=False
    )

    op.execute(
        "UPDATE review SET moderation_status = 'approved', content_version = 1, moderated_version = 1"
    )

    op.add_column("users", sa.Column("role", sa.String(), server_default="user", nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
    op.drop_index(op.f("ix_review_moderation_status"), table_name="review")
    op.drop_column("review", "moderation_enqueued_at")
    op.drop_column("review", "moderated_version")
    op.drop_column("review", "content_version")
    op.drop_column("review", "moderation_reason")
    op.drop_column("review", "moderation_status")
    op.drop_index(op.f("ix_review_moderation_review_id"), table_name="review_moderation")
    op.drop_table("review_moderation")
