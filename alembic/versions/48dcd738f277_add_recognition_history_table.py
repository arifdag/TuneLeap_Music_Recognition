"""add_recognition_history_table

Revision ID: 48dcd738f277
Revises: d22634d7e595
Create Date: 2025-06-04 10:09:10.234228

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic
revision = '48dcd738f277'
down_revision = 'd22634d7e595'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create recognition_history table
    op.create_table(
        "recognition_history",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("song_id", sa.Integer, sa.ForeignKey("songs.id"), nullable=False, index=True),
        sa.Column("recognized_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("client_info", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("recognition_history") 