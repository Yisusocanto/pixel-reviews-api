"""initial_schema

Revision ID: 398a2bf972a6
Revises:
Create Date: 2026-11-07 18:18:43.206899

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "398a2bf972a6"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "developer",
        sa.Column("igdb_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_developer_igdb_id"), "developer", ["igdb_id"], unique=True)
    op.create_index(op.f("ix_developer_name"), "developer", ["name"], unique=False)
    op.create_index(op.f("ix_developer_slug"), "developer", ["slug"], unique=True)
    op.create_table(
        "game",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("igdb_id", sa.Integer(), nullable=False),
        sa.Column("release_date", sa.DateTime(), nullable=True),
        sa.Column("image_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("background_image", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("storyline", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("critic_score", sa.Integer(), nullable=True),
        sa.Column("critic_score_count", sa.Integer(), nullable=True),
        sa.Column("igdb_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("website", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("trailer_youtube_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("trailer_title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("screenshots", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("game_modes", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("themes", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column(
            "player_perspectives", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_game_igdb_id"), "game", ["igdb_id"], unique=True)
    op.create_index(op.f("ix_game_slug"), "game", ["slug"], unique=True)
    op.create_index(op.f("ix_game_title"), "game", ["title"], unique=False)
    op.create_table(
        "genre",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_genre_slug"), "genre", ["slug"], unique=True)
    op.create_table(
        "platform",
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_platform_slug"), "platform", ["slug"], unique=True)
    op.create_table(
        "publisher",
        sa.Column("igdb_id", sa.Integer(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_publisher_igdb_id"), "publisher", ["igdb_id"], unique=True)
    op.create_index(op.f("ix_publisher_name"), "publisher", ["name"], unique=False)
    op.create_index(op.f("ix_publisher_slug"), "publisher", ["slug"], unique=True)
    op.create_table(
        "store",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_store_slug"), "store", ["slug"], unique=True)
    op.create_table(
        "users",
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
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("bio", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("google_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("profile_photo_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "gamedeveloperlink",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("developer_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["developer_id"], ["developer.id"]),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
        sa.PrimaryKeyConstraint("game_id", "developer_id"),
    )
    op.create_table(
        "gamegenrelink",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("genre_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
        sa.ForeignKeyConstraint(["genre_id"], ["genre.id"]),
        sa.PrimaryKeyConstraint("game_id", "genre_id"),
    )
    op.create_table(
        "gameplatformlink",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("platform_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
        sa.ForeignKeyConstraint(["platform_id"], ["platform.id"]),
        sa.PrimaryKeyConstraint("game_id", "platform_id"),
    )
    op.create_table(
        "gamepublisherlink",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("publisher_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
        sa.ForeignKeyConstraint(["publisher_id"], ["publisher.id"]),
        sa.PrimaryKeyConstraint("game_id", "publisher_id"),
    )
    op.create_table(
        "gamestorelink",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("game_id", "store_id"),
        sa.UniqueConstraint("game_id", "store_id", name="uq_game_store"),
    )
    op.create_table(
        "password_reset_token",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "review",
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
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("score >= 1 AND score <= 5", name="check_score"),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "game_id", name="uq_user_game"),
    )
    op.create_table(
        "wishlist",
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
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "user_id", name="uq_game_user"),
    )
    op.create_table(
        "comment",
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
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["review.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comment_review_id"), "comment", ["review_id"], unique=False)
    op.create_index(op.f("ix_comment_user_id"), "comment", ["user_id"], unique=False)
    op.create_table(
        "likes",
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
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["review.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_id", "user_id", name="uq_review_user"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("likes")
    op.drop_index(op.f("ix_comment_user_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_review_id"), table_name="comment")
    op.drop_table("comment")
    op.drop_table("wishlist")
    op.drop_table("review")
    op.drop_table("password_reset_token")
    op.drop_table("gamestorelink")
    op.drop_table("gamepublisherlink")
    op.drop_table("gameplatformlink")
    op.drop_table("gamegenrelink")
    op.drop_table("gamedeveloperlink")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_store_slug"), table_name="store")
    op.drop_table("store")
    op.drop_index(op.f("ix_publisher_slug"), table_name="publisher")
    op.drop_index(op.f("ix_publisher_name"), table_name="publisher")
    op.drop_index(op.f("ix_publisher_igdb_id"), table_name="publisher")
    op.drop_table("publisher")
    op.drop_index(op.f("ix_platform_slug"), table_name="platform")
    op.drop_table("platform")
    op.drop_index(op.f("ix_genre_slug"), table_name="genre")
    op.drop_table("genre")
    op.drop_index(op.f("ix_game_title"), table_name="game")
    op.drop_index(op.f("ix_game_slug"), table_name="game")
    op.drop_index(op.f("ix_game_igdb_id"), table_name="game")
    op.drop_table("game")
    op.drop_index(op.f("ix_developer_slug"), table_name="developer")
    op.drop_index(op.f("ix_developer_name"), table_name="developer")
    op.drop_index(op.f("ix_developer_igdb_id"), table_name="developer")
    op.drop_table("developer")
