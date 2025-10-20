"""Add subscriptions table

Revision ID: 005_add_subscriptions
Revises: 004_create_users_table
Create Date: 2025-10-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_subscriptions'
down_revision = '004_create_users_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы подписок
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='active'),
        sa.Column('plan', sa.String(length=64), nullable=True, server_default='trial'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('checks_quota', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('checks_used', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'], unique=True)
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_expires_at', 'subscriptions', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_subscriptions_expires_at')
    op.drop_index('ix_subscriptions_status')
    op.drop_index('ix_subscriptions_user_id')
    op.drop_table('subscriptions')

