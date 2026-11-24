"""add_content_reports

Revision ID: c3a9d4e7f120
Revises: 8b4e2f1a9c03
Create Date: 2026-11-23 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "c3a9d4e7f120"
down_revision: str | Sequence[str] | None = "8b4e2f1a9c03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report",
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
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), server_default="open", nullable=False),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reporter_id",
            "target_type",
            "target_id",
            name="uq_report_reporter_target",
        ),
    )
    op.create_index(op.f("ix_report_reporter_id"), "report", ["reporter_id"], unique=False)
    op.create_index(op.f("ix_report_status"), "report", ["status"], unique=False)
    op.create_index(op.f("ix_report_target_id"), "report", ["target_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_target_id"), table_name="report")
    op.drop_index(op.f("ix_report_status"), table_name="report")
    op.drop_index(op.f("ix_report_reporter_id"), table_name="report")
    op.drop_table("report")
