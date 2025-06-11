"""add_album_image

Revision ID: b90226ee2bc0
Revises: 48dcd738f277
Create Date: 2025-06-09 19:29:35.429398

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'b90226ee2bc0'
down_revision = '48dcd738f277'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('albums', sa.Column('album_image', sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column('albums', 'album_image') 