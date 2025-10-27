"""Create users table

Revision ID: 004_create_users_table
Revises: 003_add_content_html
Create Date: 2025-10-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_create_users_table'
down_revision = '003_add_content_html'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы пользователей
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_nickname', 'users', ['nickname'], unique=True)
    
    # Создание таблицы проверок (если её еще нет)
    op.create_table(
        'checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('input_media_path', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='queued'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_checks_user_id', 'checks', ['user_id'])
    op.create_index('ix_checks_created_at', 'checks', ['created_at'])
    
    # Создание таблицы сниппетов законов (если её еще нет)
    op.create_table(
        'law_snippets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('law_code', sa.String(length=128), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Удаление таблиц в обратном порядке
    op.drop_table('law_snippets')
    
    op.drop_index('ix_checks_created_at')
    op.drop_index('ix_checks_user_id')
    op.drop_table('checks')
    
    op.drop_index('ix_users_nickname')
    op.drop_index('ix_users_email')
    op.drop_table('users')

