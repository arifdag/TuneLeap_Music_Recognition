"""add_users_table

Revision ID: d22634d7e595
Revises: 20250528_create_music_metadata
Create Date: 2025-06-04 09:30:54.383750

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic
revision = 'd22634d7e595'
down_revision = '20250528_create_music_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, index=True, nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
    )
    
    # Create playlists table
    op.create_table(
        "playlists",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=func.now()),
    )
    
    # Create playlist_items table
    op.create_table(
        "playlist_items",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("playlist_id", sa.Integer, sa.ForeignKey("playlists.id"), nullable=False),
        sa.Column("song_id", sa.Integer, sa.ForeignKey("songs.id"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=func.now()),
    )


def downgrade() -> None:
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table("playlist_items")
    op.drop_table("playlists")
    op.drop_table("users") 