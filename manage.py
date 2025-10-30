#!/usr/bin/env python3
"""
Скрипт управления проектом (миграции, парсинг законов, тесты).

Использование:
    python manage.py db migrate    - создать миграцию
    python manage.py db upgrade    - применить миграции
    python manage.py db downgrade  - откатить миграцию
    python manage.py parse-law     - запустить парсер закона вручную
"""
import sys
import subprocess
from pathlib import Path


def run_alembic(command: str, *args):
    """Запуск Alembic команд"""
    cmd = ["alembic", command, *args]
    print(f"🔧 Выполняю: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "db":
        if len(sys.argv) < 3:
            print("Использование: python manage.py db [migrate|upgrade|downgrade|current]")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        
        if subcommand == "migrate":
            # Создать новую миграцию
            message = sys.argv[3] if len(sys.argv) > 3 else "auto migration"
            run_alembic("revision", "--autogenerate", "-m", message)
        
        elif subcommand == "upgrade":
            # Применить миграции
            revision = sys.argv[3] if len(sys.argv) > 3 else "head"
            run_alembic("upgrade", revision)
        
        elif subcommand == "downgrade":
            # Откатить миграцию
            revision = sys.argv[3] if len(sys.argv) > 3 else "-1"
            run_alembic("downgrade", revision)
        
        elif subcommand == "current":
            # Показать текущую версию БД
            run_alembic("current")
        
        else:
            print(f"❌ Неизвестная команда: db {subcommand}")
            sys.exit(1)
    
    elif command == "parse-law":
        # Запуск парсера закона вручную
        print("🔍 Запускаю парсер закона...")
        from backend.app.services.law_parser import parse_and_save_law
        parse_and_save_law()
        print("✅ Парсинг завершён!")

    elif command == "add-articles":
        # Запуск добавления статей вручную
        print("🔍 Начинаю добавлять статьи в бд...")
        from backend.app.init_articles import check_and_init_articles
        check_and_init_articles()
        print("✅ Статьи добавлены в бд!")
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

