"""Add last_reset_at to subscriptions

Revision ID: 007_add_last_reset_at
Revises: 006_drop_users_nickname
Create Date: 2025-10-27
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic
revision = '007_add_last_reset_at'
down_revision = '006_drop_users_nickname'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поле last_reset_at для отслеживания недельного сброса счетчика
    op.add_column('subscriptions', 
        sa.Column('last_reset_at', sa.DateTime(), nullable=True)
    )
    
    # Устанавливаем значение по умолчанию для существующих записей
    op.execute("""
        UPDATE subscriptions 
        SET last_reset_at = started_at 
        WHERE last_reset_at IS NULL
    """)
    
    # Обновляем лимиты для существующих подписок
    # Trial: 5 проверок, Pro: 20 проверок
    op.execute("""
        UPDATE subscriptions 
        SET checks_quota = 5 
        WHERE plan = 'trial' AND checks_quota != 5
    """)
    
    op.execute("""
        UPDATE subscriptions 
        SET checks_quota = 20 
        WHERE plan IN ('pro', 'premium', 'enterprise') AND checks_quota != 20
    """)


def downgrade() -> None:
    op.drop_column('subscriptions', 'last_reset_at')

