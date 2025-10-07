"""add content_html to articles

Revision ID: 003_add_content_html
Revises: 002_add_chapter_id
Create Date: 2025-10-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_content_html'
down_revision = '002_add_chapter_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('law_articles', sa.Column('content_html', sa.Text(), nullable=True))
    op.add_column('law_chapters', sa.Column('content_html', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('law_articles', 'content_html')
    op.drop_column('law_chapters', 'content_html')

