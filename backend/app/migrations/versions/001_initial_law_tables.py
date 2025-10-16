"""Initial law tables

Revision ID: 001_initial_law_tables
Revises: 
Create Date: 2025-10-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_law_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы версий закона
    op.create_table(
        'law_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('law_name', sa.String(length=512), nullable=False),
        sa.Column('law_code', sa.String(length=128), nullable=False),
        sa.Column('source_url', sa.String(length=1024), nullable=False),
        sa.Column('version_date', sa.Date(), nullable=False),
        sa.Column('parsed_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_law_versions_is_active', 'law_versions', ['is_active'])
    op.create_index('ix_law_versions_version_date', 'law_versions', ['version_date'])
    
    # Создание таблицы глав
    op.create_table(
        'law_chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['law_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_law_chapters_version_id', 'law_chapters', ['version_id'])
    
    # Создание таблицы статей
    op.create_table(
        'law_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('article_number', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('violation_type', sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['law_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_law_articles_version_id', 'law_articles', ['version_id'])
    op.create_index('ix_law_articles_article_number', 'law_articles', ['article_number'])


def downgrade() -> None:
    # Удаление в обратном порядке (из-за FK)
    op.drop_index('ix_law_articles_article_number')
    op.drop_index('ix_law_articles_version_id')
    op.drop_table('law_articles')
    
    op.drop_index('ix_law_chapters_version_id')
    op.drop_table('law_chapters')
    
    op.drop_index('ix_law_versions_version_date')
    op.drop_index('ix_law_versions_is_active')
    op.drop_table('law_versions')

