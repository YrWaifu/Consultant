"""
Alembic environment configuration.
Подключает модели SQLAlchemy и настройки БД.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.settings import settings
from backend.app.db import Base  # базовый класс для всех моделей
from backend.app.models import *  # импортируем все модели

# Alembic Config object
config = context.config

# Подключаем логирование из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData для автогенерации миграций
target_metadata = Base.metadata

# URL базы данных из .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Режим 'offline' — генерирует SQL без подключения к БД.
    Используется для генерации SQL-скриптов.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Режим 'online' — выполняет миграции с подключением к БД.
    Используется при реальной работе.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

