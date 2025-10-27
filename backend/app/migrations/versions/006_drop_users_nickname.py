"""Drop nickname column and index from users

Revision ID: 006_drop_users_nickname
Revises: 005_add_subscriptions
Create Date: 2025-10-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_drop_users_nickname'
down_revision = '005_add_subscriptions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Удаляем индекс по никнейму, если существует
    try:
        op.drop_index('ix_users_nickname', table_name='users')
    except Exception:
        pass

    # Удаляем колонку nickname, если существует
    with op.batch_alter_table('users') as batch_op:
        try:
            batch_op.drop_column('nickname')
        except Exception:
            pass


def downgrade() -> None:
    # Возвращаем колонку nickname (not null) и индекс
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('nickname', sa.String(length=100), nullable=False))
    op.create_index('ix_users_nickname', 'users', ['nickname'], unique=True)


