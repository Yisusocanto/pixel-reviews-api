"""add_comment_moderation

Revision ID: 8b4e2f1a9c03
Revises: 6a61f0f23946
Create Date: 2026-11-23 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "8b4e2f1a9c03"
down_revision: str | Sequence[str] | None = "6a61f0f23946"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "comment_moderation",
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
        sa.Column("comment_id", sa.Uuid(), nullable=False),
        sa.Column("content_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("verdict", sa.String(), nullable=False),
        sa.Column("judge", sa.String(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("scores", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=True),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["comment_id"], ["comment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_comment_moderation_comment_id"),
        "comment_moderation",
        ["comment_id"],
        unique=False,
    )

    op.add_column(
        "comment",
        sa.Column("moderation_status", sa.String(), server_default="pending", nullable=False),
    )
    op.add_column(
        "comment",
        sa.Column("moderation_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "comment",
        sa.Column("content_version", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "comment",
        sa.Column("moderated_version", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "comment",
        sa.Column("moderation_enqueued_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_comment_moderation_status"),
        "comment",
        ["moderation_status"],
        unique=False,
    )

    op.execute(
        "UPDATE comment SET moderation_status = 'approved', content_version = 1, moderated_version = 1"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_comment_moderation_status"), table_name="comment")
    op.drop_column("comment", "moderation_enqueued_at")
    op.drop_column("comment", "moderated_version")
    op.drop_column("comment", "content_version")
    op.drop_column("comment", "moderation_reason")
    op.drop_column("comment", "moderation_status")
    op.drop_index(op.f("ix_comment_moderation_comment_id"), table_name="comment_moderation")
    op.drop_table("comment_moderation")
