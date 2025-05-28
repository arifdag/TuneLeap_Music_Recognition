"""create artists, albums, songs tables

Revision ID: 20250528_create_music_metadata
Revises:
Create Date: 2025-05-28 20:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "20250528_create_music_metadata"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create artists table
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
    )

    # Create albums table
    op.create_table(
        "albums",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("release_date", sa.DateTime, nullable=True),
        sa.Column("artist_id", sa.Integer, sa.ForeignKey("artists.id"), nullable=False),
    )

    # Create songs table
    op.create_table(
        "songs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("duration", sa.Integer, nullable=True),
        sa.Column("artist_id", sa.Integer, sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("album_id", sa.Integer, sa.ForeignKey("albums.id"), nullable=True),
    )


def downgrade():
    # Drop songs table first due to foreign key constraints
    op.drop_table("songs")
    # Then drop albums table
    op.drop_table("albums")
    # Finally drop artists table
    op.drop_table("artists")
