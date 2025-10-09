"""add chapter_id to articles

Revision ID: 002_add_chapter_id
Revises: 001_initial_law_tables
Create Date: 2025-10-07 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_chapter_id'
down_revision = '001_initial_law_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавление колонки chapter_id в law_articles
    op.add_column('law_articles', sa.Column('chapter_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_law_articles_chapter_id', 
        'law_articles', 
        'law_chapters', 
        ['chapter_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_law_articles_chapter_id', 'law_articles', ['chapter_id'])


def downgrade() -> None:
    # Откат: удаление колонки и индекса
    op.drop_index('ix_law_articles_chapter_id', 'law_articles')
    op.drop_constraint('fk_law_articles_chapter_id', 'law_articles', type_='foreignkey')
    op.drop_column('law_articles', 'chapter_id')

