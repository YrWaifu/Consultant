"""create articles and article_category tables and fill data

Revision ID: 008_create_articles
Revises: 007_add_last_reset_at
Create Date: 2025-10-30 13:18:24.345728

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_create_articles'
down_revision = '007_add_last_reset_at'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы article_categories
    op.create_table(
        'article_categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(100)),
        sa.Column('sort_order', sa.Integer(), server_default='0', default=0),
    )
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('article_categories.id'), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('slug', sa.String(512), nullable=False, unique=True),
        sa.Column('excerpt', sa.Text),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')), # по умолчанию сейчас
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sort_order', sa.Integer(), server_default='0', default=0),
        sa.Column('view_count', sa.Integer(), server_default='0', default=0),
    )


def downgrade() -> None:
    op.drop_table('articles')
    op.drop_table('article_categories')

